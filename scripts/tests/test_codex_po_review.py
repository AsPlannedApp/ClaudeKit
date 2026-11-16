"""Behavior tests for the gate; isolated git repositories and fake provider processes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import signal
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'codex-po-review.sh'
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys, time
prompt=sys.stdin.read()
mode=os.environ.get('FAKE_MODE','pass')
provider=pathlib.Path(sys.argv[0]).name
if mode=='mixed':
    payload=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{\n  "repository"')+1:])[0]
    mode='sleep' if 'large.py' in payload['owned_files'] else 'p1'
with open(os.environ['CALLS'],'a') as f: f.write(provider+'\n')
if mode in ('quota','late_quota') and provider=='codex':
    if mode=='late_quota': time.sleep(1.1)
    print('ERROR: rate limit exceeded (429)',file=sys.stderr); sys.exit(1)
if mode=='empty_quota' and provider=='codex':
    pathlib.Path(sys.argv[sys.argv.index('-o')+1]).write_text('')
    print('ERROR: quota exceeded',file=sys.stderr); sys.exit(1)
if mode=='echo_quota': print('ERROR: rate limit exceeded\nERROR: authentication failed'); sys.exit(1)
if mode=='source_quota': print('ERROR: rate limit exceeded'); sys.exit(1)
if mode=='json_quota' and provider=='codex': print(json.dumps({'type':'error','message':'usage limit exceeded'})); sys.exit(1)
if mode=='nonquota': print('ERROR: authentication failed'); sys.exit(1)
if mode in ('auth','both_down') and provider=='codex':
    print('ERROR: 401 Unauthorized: not logged in. Run codex login.',file=sys.stderr); sys.exit(1)
if mode in ('claude_quota','both_down') and provider=='claude':
    print('Claude AI usage limit reached|1763290000'); sys.exit(1)
if mode=='claude_long_quota' and provider=='claude':
    print('Partial review text quoting source\n' + 'x'*400 + '\nERROR: rate limit exceeded'); sys.exit(1)
if mode=='claude_answer_then_quota' and provider=='claude':
    print(json.dumps({'decision':'FAIL','coverage_complete':True,'summary':['answer already written '+'x'*400],'findings':[],'invariants':[],'resolved':[]}))
    print('Error: rate limit exceeded',file=sys.stderr); sys.exit(1)
if mode=='claude_down_after_switch' and provider=='claude':
    # Install codex mid-run: only the disabled fallback can stop a second switch now.
    other=pathlib.Path(sys.argv[0]).with_name('codex')
    other.write_text(pathlib.Path(sys.argv[0]).read_text()); other.chmod(0o755)
    print('Claude AI usage limit reached|1763290000'); sys.exit(1)
if mode=='claude_short_verdict_quota' and provider=='claude':
    print(json.dumps({'decision':'FAIL','coverage_complete':False,'summary':['Review incomplete'],'findings':[],'invariants':[],'resolved':[]}))
    print('Error: rate limit exceeded',file=sys.stderr); sys.exit(1)
if mode=='claude_multiline_short' and provider=='claude':
    print('note\nClaude AI usage limit reached'); sys.exit(1)
if mode=='codex_answer_then_quota' and provider=='codex':
    pathlib.Path(sys.argv[sys.argv.index('-o')+1]).write_text(json.dumps({'decision':'FAIL','coverage_complete':False,'summary':['written'],'findings':[],'invariants':[],'resolved':[]}))
    print('ERROR: rate limit exceeded (429)',file=sys.stderr); sys.exit(1)
if mode=='claude_auth' and provider=='claude':
    print('Invalid API key \u00b7 Please run /login'); sys.exit(1)
if mode in ('sleep','late_quota'):
    if mode=='sleep':
        import subprocess
        child=subprocess.Popen(['sleep','30'])
        pathlib.Path(os.environ['CHILD']).write_text(str(child.pid))
    time.sleep(30)
if mode=='malformed': answer='DECISION: PASS\nnot JSON'
else:
    data=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{\n  "repository"')+1:])[0]
    findings=[]
    if mode in ('p1','p2','p3','contradict','bad_site'):
        severity={'p1':'P1','p2':'P2','p3':'P3','contradict':'P1','bad_site':'P2'}[mode]
        findings=[{'class':'budget','severity':severity,'impact':'Concrete input and consequence','instances':[{'path':'app.py','line':1}]}]
    answer=json.dumps({'decision':'FAIL' if mode=='p1' else 'PASS','coverage_complete':True,
      'summary':['Checked assigned sites'],'findings':findings,
      'invariants':[{'id':x['id'],'status':'confirmed','evidence':'app.py:1 checked'} for x in data['assigned_invariant_evidence']],
      'resolved':[{'id':x['id'],'evidence':'app.py:1 corrected'} for x in data['previous_P1']] if mode=='resolve' else []})
if mode in ('incomplete','drop_checks','bad_resolution','bad_site','boolean_evidence'):
    value=json.loads(answer)
    if mode=='boolean_evidence': value['resolved']=[{'id':x['id'],'evidence':True} for x in data['previous_P1']]
    if mode=='incomplete': value['coverage_complete']=False; value['decision']='FAIL'
    if mode=='drop_checks': value['invariants']=[]
    if mode=='bad_resolution': value['resolved']=[{'id':'invented','evidence':'guess'}]
    if mode=='bad_site': value['findings'][0]['instances'][0]['path']='../outside'
    answer=json.dumps(value)
if provider=='codex':
    pathlib.Path(sys.argv[sys.argv.index('-o')+1]).write_text(answer)
    print('echoed old transcript: DECISION: PASS')
else: print(answer)
'''


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        for cmd in (['init', '-q'], ['config', 'user.email', 'gate@test.local'], ['config', 'user.name', 'Gate']):
            self.git(*cmd)
        (self.repo / 'app.py').write_text('original\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'initial')
        self.base = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'app.py').write_text('changed\n')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ('codex', 'claude'):
            path = self.bin / name
            path.write_text(FAKE)
            path.chmod(0o755)
        self.env = dict(os.environ, CODEX_PO_WORKSPACE_ROOT=str(self.root), CODEX_PO_REPOS='repo',
                        PO_LOG_ROOT=str(self.root / 'logs'), PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        CALLS=str(self.root / 'calls'), CHILD=str(self.root / 'child'), REVIEW_TIMEOUT_SECONDS='10')
        self.brief = self.root / 'brief.md'
        self.brief.write_text('Request, plan, implementation')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True, stderr=subprocess.STDOUT)

    def gate(self, *args, mode='pass', **env):
        return subprocess.run(['bash', str(SCRIPT), '--context-file', str(self.brief), *args], env=dict(self.env, FAKE_MODE=mode, **env),
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)

    def runs(self):
        return sorted((self.root / 'logs').glob('*/metrics.json'))

    def test_brief_limits_and_launch_guard(self):
        for n, expected in [(1900, 0), (2000, 0), (2001, 2), (0, 2)]:
            self.brief.write_text('é' * n)
            result = self.gate('--session', f'brief-{n}')
            self.assertEqual(result.returncode, expected, result.stdout)
        # Skill's shell guard counts characters, not UTF-8 bytes.
        for n in (1900, 1901):
            self.brief.write_text('x' * n)
            p = subprocess.run(['bash', '-c', 'n=$(wc -m < "$1"); [ "$n" -le 1900 ]', 'guard', str(self.brief)])
            self.assertEqual(p.returncode, int(n > 1900))

    def test_severity_followups_and_final_answer_only(self):
        for mode, code in [('pass', 0), ('p1', 1), ('p2', 0), ('p3', 0), ('malformed', 1), ('contradict', 1), ('incomplete', 1), ('bad_resolution', 1), ('bad_site', 1)]:
            result = self.gate('--session', mode, mode=mode)
            self.assertEqual(result.returncode, code, result.stdout)
        text = '\n'.join(p.read_text() for p in (self.root / 'logs').glob('*/follow-ups.md'))
        self.assertIn('P2 — budget', text)
        self.assertIn('P3 — budget', text)

    def test_repos_and_base(self):
        self.assertEqual(self.gate('--repos', 'missing').returncode, 2)
        self.assertEqual(self.gate('--repos', 'repo,repo').returncode, 2)
        self.git('add', '.')
        self.git('commit', '-qm', 'change')
        self.assertIn('nothing to review', self.gate('--repos', 'repo').stdout)
        self.assertEqual(self.gate('--base', self.base, '--session', 'base').returncode, 0)
        (self.repo / 'app.py').write_text('next\n')
        result = self.gate('--base', 'missing-ref', '--session', 'fallback-base')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('reviewing uncommitted', result.stdout)

    def test_quota_only_fallback(self):
        result = self.gate('--reviewer', 'auto', '--session', 'quota', mode='quota')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex', 'claude'])
        result = self.gate('--session', 'empty-final', mode='empty_quota')
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.gate('--session', 'json-error', mode='json_quota')
        self.assertEqual(result.returncode, 0, result.stdout)
        for mode in ('nonquota', 'p1', 'malformed', 'echo_quota', 'source_quota'):
            (self.root / 'calls').write_text('')
            result = self.gate('--reviewer', 'auto', '--session', mode, mode=mode)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex'])
        (self.root / 'calls').write_text('')
        self.assertEqual(self.gate('--reviewer', 'codex', '--session', 'explicit-fallback', mode='quota').returncode, 0)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex', 'claude'])
        (self.root / 'calls').write_text('')
        self.assertEqual(self.gate('--reviewer', 'codex', '--fallback', 'off', '--session', 'no-fallback', mode='quota').returncode, 1)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex'])
        (self.root / 'calls').write_text('')
        self.assertEqual(self.gate('--session', 'env-off', mode='quota', PO_FALLBACK='off').returncode, 1)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex'])
        self.assertEqual(self.gate('--reviewer', 'claude', '--session', 'explicit').returncode, 0)

    def test_cap_and_persistent_findings(self):
        self.assertEqual(self.gate('--session', 'cap', mode='p1').returncode, 1)
        self.assertEqual(self.gate('--session', 'cap').returncode, 2)
        self.assertEqual(self.gate('--session', 'cap', '--base', self.base).returncode, 1)
        self.assertEqual(self.gate('--session', 'cap', '--base', self.base).returncode, 3)
        calls = (self.root / 'calls').read_text()
        self.assertEqual(self.gate('--session', 'cap', '--base', self.base).returncode, 3)
        self.assertEqual((self.root / 'calls').read_text(), calls)
        self.assertEqual(self.gate('--session', 'fixed', mode='p1').returncode, 1)
        result = self.gate('--session', 'fixed', '--base', self.base, mode='resolve')
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_audit_and_whole_file_coverage(self):
        (self.repo / 'large.py').write_text('body\n' * 450)
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests' / 'test_app.py').write_text('test\n' * 40)
        audit = {'invariants': [{'id':f'I{i}', 'statement':'Invariant', 'search':'rg pattern app.py', 'evidence':'app.py:1',
                 'sites':[{'repo':'repo','path':'app.py','line':1}],
                 'tests':[{'repo':'repo','path':'tests/test_app.py','name':'case','result':'not run'}]} for i in range(5)]}
        file = self.root / 'audit.json'
        file.write_text(json.dumps(audit))
        result = self.gate('--audit-file', str(file))
        self.assertEqual(result.returncode, 0, result.stdout)
        run = self.runs()[0].parent
        diffs = [p.read_text() for p in run.glob('*.diff')]
        self.assertEqual(sum(t.count('+body\n') for t in diffs), 450)
        self.assertEqual(sum('diff --git a/large.py' in t for t in diffs), 1)
        result = self.gate('--session', 'missing-checks', '--audit-file', str(file), mode='drop_checks')
        self.assertEqual(result.returncode, 1, result.stdout)
        metrics = json.loads((run / 'metrics.json').read_text())
        covered = set()
        for part in metrics['parts']:
            prompt = (run / (part['unit'] + '-prompt.md')).read_text()
            data = json.JSONDecoder().raw_decode(prompt[prompt.index('\n{\n  "repository"')+1:])[0]
            covered.update(data['owned_files'])
        self.assertEqual(covered, {'app.py', 'large.py', 'tests/test_app.py'})
        assigned = {c for part in metrics['parts'] for c in part['classes']}
        self.assertEqual(assigned, {f'I{i}' for i in range(5)})
        self.assertTrue(any(p['classes'] == [f'I{i}' for i in range(5)] for p in metrics['parts']))
        audit['invariants'][0]['sites'][0]['path'] = '../escape'
        file.write_text(json.dumps(audit))
        self.assertEqual(self.gate('--audit-file', str(file)).returncode, 2)

    def test_untracked_directory_symlink_is_reviewed_without_following_target(self):
        target = self.root / 'canonical'
        target.mkdir()
        (target / 'SKILL.md').write_text('DO_NOT_INLINE_TARGET_CONTENT\n')
        parent = self.repo / '.agents'
        parent.mkdir()
        (parent / 'skills').symlink_to('../../canonical', target_is_directory=True)
        result = self.gate('--session', 'directory-link')
        self.assertEqual(result.returncode, 0, result.stdout)
        run = self.runs()[0].parent
        diffs = '\n'.join(p.read_text() for p in run.glob('*.diff'))
        self.assertIn('new file mode 120000', diffs)
        self.assertIn('+../../canonical', diffs)
        self.assertNotIn('Could not access', diffs)
        self.assertNotIn('DO_NOT_INLINE_TARGET_CONTENT', diffs)
        parsed = subprocess.run(['git', 'apply', '--numstat', '-'], input=diffs, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(parsed.returncode, 0, parsed.stderr)
        self.assertIn('.agents/skills', parsed.stdout)
        self.assertIn('.agents/skills', json.loads((run / 'repo.files.json').read_text())['files'])

    def test_repo_part_is_not_assigned_other_repositories_invariants(self):
        audit = {'invariants': [
            {'id': f'I{i}', 'statement': 'Invariant', 'search': 'read app.py', 'evidence': 'app.py:1',
             'sites': [{'repo': 'repo' if i == 0 else 'other', 'path': 'app.py', 'line': 1}],
             'tests': [{'repo': 'repo' if i == 0 else 'other', 'path': 'test.py', 'name': 'case', 'result': 'not run'}]}
            for i in range(5)
        ]}
        file = self.root / 'audit.json'
        file.write_text(json.dumps(audit))
        result = self.gate('--session', 'local-ownership', '--repos', 'repo', '--audit-file', str(file),
                           CODEX_PO_REPOS='repo other')
        self.assertEqual(result.returncode, 0, result.stdout)
        metrics = json.loads(self.runs()[0].read_text())
        self.assertEqual([part['classes'] for part in metrics['parts']], [['I0']])

    def test_deadline_queue_and_child_cleanup(self):
        (self.repo / 'second.py').write_text('body\n' * 500)
        started = time.monotonic()
        result = self.gate(mode='sleep', REVIEW_TIMEOUT_SECONDS='2', PO_MAX_PARALLEL='1')
        self.assertEqual(result.returncode, 124, result.stdout)
        self.assertLess(time.monotonic() - started, 3)
        metrics = json.loads(self.runs()[0].read_text())
        self.assertEqual(metrics['model_calls'], 1)
        self.assertEqual(len(metrics['parts']), 2)
        pid = int((self.root / 'child').read_text())
        ps = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], text=True, stdout=subprocess.PIPE)
        self.assertTrue(ps.returncode or ps.stdout.strip().startswith('Z'), ps.stdout)

    def test_late_fallback_shares_deadline(self):
        started = time.monotonic()
        result = self.gate(mode='late_quota', REVIEW_TIMEOUT_SECONDS='2')
        self.assertEqual(result.returncode, 124, result.stdout)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex', 'claude'])

    def test_fallback_is_two_way_for_quota_and_auth(self):
        cases = [('codex', 'quota', ['codex', 'claude'], 'quota'), ('codex', 'auth', ['codex', 'claude'], 'auth'),
                 ('claude', 'claude_quota', ['claude', 'codex'], 'quota'),
                 ('claude', 'claude_auth', ['claude', 'codex'], 'auth')]
        for reviewer, mode, calls, reason in cases:
            (self.root / 'calls').write_text('')
            result = self.gate('--reviewer', reviewer, '--session', mode, mode=mode)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual((self.root / 'calls').read_text().splitlines(), calls, mode)
            metrics = json.loads(self.runs()[-1].read_text())
            self.assertEqual([a['reviewer'] for a in metrics['parts'][0]['attempts']], calls)
            self.assertEqual(metrics['parts'][0]['fallback'], {'from': calls[0], 'to': calls[1], 'reason': reason})

    def test_claude_answer_or_long_output_blocks_fallback(self):
        for mode in ('claude_long_quota', 'claude_answer_then_quota', 'claude_short_verdict_quota', 'claude_multiline_short'):
            (self.root / 'calls').write_text('')
            result = self.gate('--reviewer', 'claude', '--session', mode, mode=mode)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual((self.root / 'calls').read_text().splitlines(), ['claude'], mode)

    def test_written_codex_answer_blocks_fallback(self):
        result = self.gate('--reviewer', 'codex', mode='codex_answer_then_quota')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex'])

    def test_invalid_fallback_value_is_rejected(self):
        self.assertEqual(self.gate('--fallback', 'maybe').returncode, 2)
        self.assertEqual(self.gate(PO_FALLBACK='maybe').returncode, 2)
        self.assertFalse((self.root / 'calls').exists())

    def test_fallback_runs_at_most_once(self):
        result = self.gate('--reviewer', 'codex', mode='both_down')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex', 'claude'])

    def test_missing_cli_falls_back_to_the_other(self):
        self.env['PATH'] = str(self.bin) + os.pathsep + '/usr/bin:/bin'
        for missing, reviewer, used in (('codex', 'auto', 'claude'), ('claude', 'claude', 'codex')):
            for name in ('codex', 'claude'):
                (self.bin / name).write_text(FAKE)
                (self.bin / name).chmod(0o755)
            (self.bin / missing).unlink()
            (self.root / 'calls').write_text('')
            result = self.gate('--reviewer', reviewer, '--session', 'missing-' + missing)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn(f'{missing} CLI not found', result.stdout)
            self.assertEqual((self.root / 'calls').read_text().splitlines(), [used])
            metrics = json.loads(self.runs()[-1].read_text())
            self.assertEqual(metrics['parts'][0]['fallback'], {'from': missing, 'to': used, 'reason': 'missing-cli'})

    def test_missing_cli_switch_consumes_the_one_fallback(self):
        self.env['PATH'] = str(self.bin) + os.pathsep + '/usr/bin:/bin'
        (self.bin / 'codex').unlink()
        result = self.gate('--reviewer', 'codex', mode='claude_down_after_switch')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['claude'])
        (self.bin / 'codex').unlink()
        (self.root / 'calls').unlink()
        result = self.gate('--reviewer', 'codex', '--session', 'env-off', PO_FALLBACK='off')
        self.assertEqual(result.returncode, 127, result.stdout)
        self.assertFalse((self.root / 'calls').exists())

    def test_missing_cli_without_fallback_or_alternative(self):
        self.env['PATH'] = str(self.bin) + os.pathsep + '/usr/bin:/bin'
        (self.bin / 'codex').unlink()
        result = self.gate('--reviewer', 'codex', '--fallback', 'off')
        self.assertEqual(result.returncode, 127, result.stdout)
        (self.bin / 'claude').unlink()
        result = self.gate('--reviewer', 'codex')
        self.assertEqual(result.returncode, 127, result.stdout)
        self.assertFalse((self.root / 'calls').exists())

    def test_model_only_largest_first_round(self):
        (self.repo / 'large.py').write_text('body\n' * 450)
        result = self.gate('--session', 'model', '--first-round-model', 'gpt-6-astra')
        self.assertEqual(result.returncode, 0, result.stdout)
        first = json.loads(self.runs()[0].read_text())
        self.assertEqual(sum(p['model'] == 'gpt-6-astra' for p in first['parts']), 1)
        result = self.gate('--session', 'model', '--base', self.base, '--first-round-model', 'gpt-6-astra')
        self.assertEqual(result.returncode, 0, result.stdout)
        second = json.loads(self.runs()[1].read_text())
        self.assertTrue(all(p['model'] == 'configured default' for p in second['parts']))

    def test_delta_rejects_reopening_full_branch(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'feature')
        result = self.gate('--session', 'delta-base', '--base', self.base)
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.gate('--session', 'delta-base', '--base', self.base)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('previous reviewed commit', result.stdout)
        missing = self.gate('--session', 'delta-base', '--base', 'missing-ref')
        self.assertEqual(missing.returncode, 2, missing.stdout)
        self.assertIn('refusing to omit committed changes', missing.stdout)
        previous = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'app.py').write_text('fix\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fix')
        result = self.gate('--session', 'delta-base', '--base', previous)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_interrupt_cleanup_and_concurrent_session_lock(self):
        command = ['bash', str(SCRIPT), '--session', 'concurrent']
        env = dict(self.env, FAKE_MODE='sleep')
        first = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.monotonic() + 5
            while not (self.root / 'child').exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((self.root / 'child').exists())
            second = self.gate('--session', 'concurrent')
            self.assertEqual(second.returncode, 2, second.stdout)
            self.assertIn('already has an active round', second.stdout)
            self.assertEqual((self.root / 'calls').read_text().splitlines(), ['codex'])
            first.send_signal(signal.SIGTERM)
            output, _ = first.communicate(timeout=3)
            self.assertEqual(first.returncode, 143, output)
            self.assertIn('process groups terminated', output)
            pid = int((self.root / 'child').read_text())
            ps = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], text=True, stdout=subprocess.PIPE)
            self.assertTrue(ps.returncode or ps.stdout.strip().startswith('Z'), ps.stdout)
        finally:
            if first.poll() is None:
                first.send_signal(signal.SIGTERM)
                first.communicate(timeout=3)

    def test_interrupted_round_recovers_completed_p1(self):
        (self.repo / 'large.py').write_text('body\n' * 450)
        command = ['bash', str(SCRIPT), '--session', 'recovery']
        first = subprocess.Popen(command, env=dict(self.env, FAKE_MODE='mixed'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.monotonic() + 5
            completed = []
            while time.monotonic() < deadline:
                completed = list((self.root / 'logs').glob('*/*.result.json'))
                if completed and (self.root / 'child').exists(): break
                time.sleep(.02)
            self.assertTrue(completed)
            first.send_signal(signal.SIGTERM)
            first.communicate(timeout=3)
            result = self.gate('--session', 'recovery', '--base', self.base)
            self.assertEqual(result.returncode, 1, result.stdout)
            state = json.loads(next((self.root / 'logs' / 'sessions').glob('*.json')).read_text())
            self.assertTrue(state['open_p1'])
            self.assertEqual(state['rounds'][0]['status'], 'RECOVERED_INTERRUPTION')
        finally:
            if first.poll() is None:
                first.send_signal(signal.SIGTERM)
                first.communicate(timeout=3)

    def test_unfinished_scope_survives_empty_delta(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'feature')
        feature = self.git('rev-parse', 'HEAD').strip()
        first = self.gate('--session', 'unfinished', '--base', self.base, mode='incomplete')
        self.assertEqual(first.returncode, 1, first.stdout)
        second = self.gate('--session', 'unfinished', '--base', feature)
        self.assertEqual(second.returncode, 0, second.stdout)
        self.assertNotIn('nothing to review', second.stdout)
        metrics = json.loads(self.runs()[1].read_text())
        self.assertEqual(metrics['model_calls'], 1)
        diff = next(self.runs()[1].parent.glob('*.diff')).read_text()
        self.assertIn('+changed', diff)
        state = json.loads(next((self.root / 'logs' / 'sessions').glob('*.json')).read_text())
        self.assertFalse(state['coverage_debt'])

    def test_followups_persist_with_provenance(self):
        self.assertEqual(self.gate('--session', 'followup', mode='p2').returncode, 0)
        result = self.gate('--session', 'followup', '--base', self.base)
        self.assertEqual(result.returncode, 0, result.stdout)
        followup = (self.runs()[1].parent / 'follow-ups.md').read_text()
        self.assertIn('P2 — budget', followup)
        self.assertIn('Source: round 1', followup)
        self.assertIn('.result.json', followup)

    def test_boolean_resolution_is_not_evidence(self):
        self.assertEqual(self.gate('--session', 'boolean', mode='p1').returncode, 1)
        result = self.gate('--session', 'boolean', '--base', self.base, mode='boolean_evidence')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('invalid prior finding resolution', result.stdout)

    def test_uncommitted_deletion_scope_is_frozen_before_commit(self):
        (self.repo / 'app.py').unlink()
        first = self.gate('--session', 'deletion', mode='incomplete')
        self.assertEqual(first.returncode, 1, first.stdout)
        self.git('add', '-u')
        self.git('commit', '-qm', 'remove feature')
        second = self.gate('--session', 'deletion', '--base', self.base)
        self.assertEqual(second.returncode, 0, second.stdout)
        diff = next(self.runs()[1].parent.glob('*.diff')).read_text()
        self.assertIn('-original', diff)
        self.assertIn('deleted file mode', diff)

    def test_repo_subset_cannot_clear_other_repo_coverage(self):
        other = self.root / 'other'
        other.mkdir()
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        subprocess.run(['git', '-C', str(other), '-c', 'user.name=Gate', '-c', 'user.email=gate@test.local', 'commit', '--allow-empty', '-qm', 'initial'], check=True)
        self.env['CODEX_PO_REPOS'] = 'repo other'
        first = self.gate('--session', 'subset', '--repos', 'repo', mode='incomplete')
        self.assertEqual(first.returncode, 1, first.stdout)
        second = self.gate('--session', 'subset', '--repos', 'other', '--base', self.base)
        self.assertEqual(second.returncode, 1, second.stdout)
        (other / 'file.txt').write_text('new content\n')
        third = self.gate('--session', 'subset', '--repos', 'other', '--base', self.base)
        self.assertEqual(third.returncode, 1, third.stdout)
        state = json.loads(next((self.root / 'logs' / 'sessions').glob('*.json')).read_text())
        self.assertIn('repo', state['coverage_debt'])

    def test_legacy_symbolic_debt_rejects_inference_after_commit(self):
        (self.repo / 'app.py').unlink()
        self.assertEqual(self.gate('--session', 'legacy', mode='incomplete').returncode, 1)
        state_path = next((self.root / 'logs' / 'sessions').glob('*.json'))
        state = json.loads(state_path.read_text())
        state['coverage_debt']['repo']['base'] = 'HEAD'
        metadata_path = Path(state['rounds'][0]['output']) / 'repo.files.json'
        metadata = json.loads(metadata_path.read_text())
        metadata['base'] = 'HEAD'
        metadata_path.write_text(json.dumps(metadata))
        state_path.write_text(json.dumps(state))
        self.git('add', '-u')
        self.git('commit', '-qm', 'remove feature')
        calls = (self.root / 'calls').read_text()
        result = self.gate('--session', 'legacy', '--base', self.base)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('restore the original immutable review base', result.stdout)
        self.assertEqual((self.root / 'calls').read_text(), calls)
        self.assertEqual(json.loads(state_path.read_text())['coverage_debt']['repo']['base'], 'HEAD')

    def test_legacy_symbolic_debt_without_origin_fails_closed(self):
        self.assertEqual(self.gate('--session', 'legacy-unknown', mode='incomplete').returncode, 1)
        state_path = next((self.root / 'logs' / 'sessions').glob('*.json'))
        state = json.loads(state_path.read_text())
        state['coverage_debt']['repo']['base'] = 'HEAD'
        state_path.write_text(json.dumps(state))
        calls = (self.root / 'calls').read_text()
        result = self.gate('--session', 'legacy-unknown', '--base', self.base)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('no unambiguous original commit', result.stdout)
        self.assertEqual((self.root / 'calls').read_text(), calls)

    def test_invalid_timeout(self):
        self.assertEqual(self.gate(REVIEW_TIMEOUT_SECONDS='181').returncode, 2)

    def test_preparation_timeout(self):
        real_git = subprocess.check_output(['which', 'git'], text=True).strip()
        fake_git = self.bin / 'git'
        fake_git.write_text('#!/bin/sh\nsleep 30\nexec ' + real_git + ' "$@"\n')
        fake_git.chmod(0o755)
        started = time.monotonic()
        result = self.gate(REVIEW_TIMEOUT_SECONDS='1')
        self.assertEqual(result.returncode, 124, result.stdout)
        self.assertLess(time.monotonic() - started, 2)
        self.assertFalse((self.root / 'calls').exists())


if __name__ == '__main__':
    unittest.main()

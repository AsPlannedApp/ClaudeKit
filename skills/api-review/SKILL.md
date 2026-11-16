---
description: Review an API endpoint or its consumers for REST convention compliance. Use whenever code touches an API route, response shape, controller, API-collection request, or a client that reads API data.
---

# /api-review — REST convention review

This skill is self-contained. It ships with a **default house standard** that worked well across
several backends (PHP and JS) and an SPA. **Edit the standard section to match your project**,
then keep it as the single source of truth. `{{…}}` marks a placeholder.

---

## House standard

### Response envelopes

```jsonc
// Single resource: GET 200 / POST 201 (+ Location header)
{ "success": true, "status": 200, "message": "success",
  "element": { "id": "…" },
  "includes": { }            // optional: sideloaded lookup data only
}

// Multiple resources: GET 200
{ "success": true, "status": 200, "message": "success", "collection": [ ] }

// Paginated: `pagination` is present alongside `collection`, absent otherwise
{ "success": true, "status": 200, "message": "success", "collection": [ ],
  "pagination": { "currentPage": 1, "totalPages": 4, "totalItems": 37,
                  "perPage": 10, "hasNext": true, "hasPrev": false } }
// No results: currentPage 1, totalPages 1, totalItems 0, hasNext/hasPrev false.
// A missing ?page defaults to 1 (never a 422).

// PUT / DELETE success: 204 with an EMPTY body (no JSON at all)

// Validation error: 422
{ "success": false, "status": 422, "message": "Validation errors",
  "errors": [ { "message": "Email is invalid" } ] }

// Single error (401, 403, 404, 409, 500…): no errors array
{ "success": false, "status": 404, "message": "Not found" }

// 405: JSON body + Allow header
{ "success": false, "status": 405, "message": "Method not allowed" }
```

### Verbs and status codes

| Verb | On | Success |
|---|---|---|
| GET | element or collection | 200 |
| POST | collection (creates) | 201 + `Location` |
| PUT | element (full update) | 204, empty body |
| DELETE | element | 204, empty body |

These codes have fixed meanings: 400 for malformed input; 401 when unauthenticated; 403 when
authenticated but not allowed; 404 when not found (never 401); 409 for a conflict; 422 for a
validation failure (never 406); 429 for rate limiting, with `Retry-After`; 500 for an unhandled
error; 501 for a stub.

### URLs

- Collections end with `/` (`/users/`). Elements don't (`/users/{id}`).
- No verbs in paths (❌ `/auth/delete`). A pragmatic exception needs a recorded reason.
- A malformed id (e.g. not a UUID) returns 404 or 422, never 500.

### Content type

`{{application/vnd.<product>.<resource>.v1+json}}`, with the error type
`{{application/vnd.<product>.error.v1+json}}`.

### Helpers

Every controller uses the project's response helper (`{{ApiResponse::element / collection /
noContent / invalid / error}}`), never raw JSON responses. A 204 goes through the "no content"
helper, never an element helper with an empty body.

### Recorded exceptions

Deliberate deviations (e.g. "autosave PUT returns 200 with the new revision, so saves can
chain") are listed in `{{API_EXCEPTIONS.md}}` with their reasons. A deviation that isn't listed
there is a finding.

---

## Checklist

Mark each item ✅ or ❌, with evidence:

1. **Verb:** correct for the operation; no verb in the URL.
2. **URL:** collection/element shape, consistent naming with neighbouring routes.
3. **Auth:** protected routes require auth; public ones are explicitly listed as public; 401
   carries the `status` field.
4. **Request:** validated before use; 422 with an `errors` array; no unexpected fields accepted or
   leaked back.
5. **Status:** follows the verb table; not-found is 404; validation is 422.
6. **Envelope:** `success`/`status`/`message` present; `success` matches 2xx; `element` or
   `collection` (no legacy keys); 204 has no body.
7. **Pagination:** the full object on paginated collections; absent elsewhere; empty-results
   values; page default.
8. **405:** a JSON body plus an `Allow` header, handled centrally.
9. **Content type:** the vendor type, and the error type on errors.
10. **API collection** ({{Bruno / Postman / Hurl}}): the request exists; tests assert status and
    shape; token extraction reads the envelope path.
11. **Consumers:** every client that reads this response uses the right path (`element.x`, not
    `x`), handles 204 without parsing JSON, and handles 422 `errors[]`.

---

## How to run a review

1. **Identify the change:** verb, path, which backend, and whether it needs auth.
2. **Read the route and the handler/controller.** Read the real code, not docs about it.
3. **Find every consumer:** grep the clients for the path and the response fields they read.
4. **Execute the affected collection requests** against the **local** environment only
   (`{{bru run <folder> --env local}}`). Report the actual statuses.
5. **Report** a table:

   | Category | Status | Finding |
   |---|---|---|
   | Verb | ✅ | POST on a collection |
   | Status | ❌ | Returns 406; should be 422 (`path:line`) |
   | Consumer | ❌ | Reads `res.content`; should be `res.element` (`path:line`) |

6. **Fix** the handler, the collection and the consumers together. One fixed violation means
   searching the other routes for the same class of violation.
7. **Say what was executed and what was only read.**

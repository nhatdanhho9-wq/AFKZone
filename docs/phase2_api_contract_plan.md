# Phase 2 - API Contract Lock Plan

Goal: Lock a single, versioned API contract so server, client, and docs stay in sync. No breaking changes without a version bump.

Scope:
- All public HTTP endpoints used by client/admin.
- Webhooks: /payment/bank/webhook and /webhook/casso (decide canonical).
- Auth rules: admin_key vs JWT, headers, errors.
- Response schema, error schema, pagination, date/time format.

Deliverables:
- Contract spec (OpenAPI preferred) + examples.
- Contract tests (smoke + webhook signature tests).
- Server code aligned to contract.
- Client code aligned to contract.
- Deprecation notes + versioning rules.

Plan Table
| ID | Task | Owner | Priority | Dependency | Definition of Done |
| --- | --- | --- | --- | --- | --- |
| 2.0 | Freeze endpoint inventory (server + client) | Opus | P0 | Phase 1 done | Single list of endpoints, methods, auth, params |
| 2.1 | Pick canonical webhook endpoint | Opus + PM | P0 | 2.0 | Decision recorded, other endpoint marked deprecated |
| 2.2 | Choose canonical date/time format | Opus + PM | P0 | 2.0 | All timestamps use one format (ISO or epoch ms) |
| 2.3 | Define error schema | Opus | P0 | 2.0 | Standard error response across all endpoints |
| 2.4 | Define pagination schema | Opus | P0 | 2.0 | Standard page/limit/total in all list endpoints |
| 2.5 | Draft OpenAPI spec | Opus | P0 | 2.1-2.4 | Spec covers all endpoints + auth + errors |
| 2.6 | Add examples to spec | Opus | P1 | 2.5 | Example request/response for key endpoints |
| 2.7 | Align server to spec | Opus | P0 | 2.5 | Server responses match spec, no mismatch |
| 2.8 | Align client to spec | Opus | P0 | 2.5 | Client uses canonical endpoints + schema |
| 2.9 | Add contract tests (smoke) | Opus | P0 | 2.5 | Tests cover top 10 endpoints |
| 2.10 | Add webhook signature tests | Opus | P0 | 2.1 | Invalid signature -> 401, valid -> 200 |
| 2.11 | Add CI gate for contract | Opus | P1 | 2.9 | CI fails if spec != code |
| 2.12 | Add versioning rule | Opus + PM | P1 | 2.5 | Documented rule for breaking changes |
| 2.13 | Write deprecation plan | Opus | P1 | 2.1 | Deprecated endpoints listed with removal date |
| 2.14 | Release notes for Phase 2 | Opus | P2 | 2.7-2.13 | Summary of changes + migration notes |

Definition of Done (Phase 2)
- OpenAPI spec is complete and matches server responses.
- Client uses the canonical endpoints and schema.
- Contract tests pass in CI.
- Deprecated endpoints are documented.
- Webhook signature behavior is tested and verified.

Open Questions (to answer before 2.1)
- Canonical webhook: /payment/bank/webhook or /webhook/casso?
- Timestamp format: ISO 8601 or epoch ms?
- Auth: keep both admin_key and JWT or migrate to JWT only?

# Phase 2: API Contract Lock Implementation Plan

## Goal
Establish a strict, versioned API contract to ensure server-client synchronization and prevent regressions.

## Decisions (Approved)
- **Canonical Webhook**: `/webhook/casso`
- **Timestamp Format**: **ISO 8601** (e.g., `2023-10-27T10:00:00`)
- **Authentication**: Keep **Admin Key** (scripts) + **JWT** (Dashboard/Client)

## Execution Steps

### 1. Inventory & Canonicalization (Tasks 2.0 - 2.2)
- [ ] **Freeze Inventory**: Update `docs/inventory/endpoints_baseline.md` to reflect current state after Phase 1 changes.
- [ ] **Canonical Webhook**: 
    - Mark `/payment/bank/webhook` as **DEPRECATED** in code and docs.
    - Ensure `/webhook/casso` is the primary documented endpoint.
- [ ] **Timestamp Standardization**:
    - Audit all endpoints returning dates.
    - Ensure `isoformat()` is used consistently.

### 2. Schema Definition (Tasks 2.3 - 2.6)
- [ ] **Error Schema**: Define a standard error response structure (e.g., `{ "error": "message", "code": 4xx }`).
- [ ] **Pagination**: Define standard query params (`page`, `limit`) and response wrapper (`items`, `total`, `page`).
- [ ] **OpenAPI Spec**: Create `docs/openapi.yaml` documenting all public endpoints.

### 3. Usage Alignment (Tasks 2.7 - 2.8)
- [ ] **Server Alignment**: Refactor server code to match the defined schemas (dates, errors).
- [ ] **Client Alignment**: Update Flutter client to use canonical endpoints and parse standard responses.

### 4. Verification & Process (Tasks 2.9 - 2.14)
- [ ] **Contract Tests**: Create `tests/test_contract.py` to validate key endpoints against the spec.
- [ ] **Webhook Tests**: Add specific tests for strict signature verification.
- [ ] **Deprecation Plan**: Document timeline for removing deprecated endpoints.
- [ ] **Versioning**: Establish rule: Breaking change = URL version bump (v3).

## Proposed Changes

### Documentation
- `docs/inventory/endpoints_baseline.md` -> `docs/inventory/endpoints_v2.2.md`
- New: `docs/openapi.yaml`

### Code (`server_app.py`)
- Add `@deprecated` warnings or comments to old endpoints.
- Standardize date formatting in all response models.
- Implement standard `HTTPException` handlers to return consistent JSON.

### Client
- Verify usage of `/webhook/casso` (if client generates QR with callback) - logic check.
- Ensure date parsing handles ISO 8601 robustly.

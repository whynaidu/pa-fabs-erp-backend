# PA FABS ERP — Test Case Document

| | |
|---|---|
| **Project** | PA FABS Textile ERP (v2.0) |
| **Frontend** | https://pa-fabs-erp-frontend.vercel.app |
| **Backend** | https://pa-fabs-erp-backend.onrender.com |
| **Test type** | Functional, UI (Chrome), API, Authorization, Negative/Edge |
| **Approach** | Each case executed live; Actual result recorded. UI cases driven through the real frontend. |
| **Test data** | Seeded users `admin/admin123` (admin), `user/user123` (staff). |
| **Legend** | ✅ Pass · ❌ Fail · P=Positive, N=Negative, E=Edge |

Summary: **62 test cases executed — 62 Pass, 0 open Fail.** 8 defects were found during testing and **all fixed & re-verified** (see Defect Log at the end).

---

## 1. Authentication & Session

| ID | Type | Title | Preconditions | Steps | Test Data | Expected | Actual | Status |
|----|------|-------|---------------|-------|-----------|----------|--------|--------|
| TC-AUTH-01 | P | Staff login | On login screen | Select "Staff", enter creds, Sign In | user/user123 | Enters Staff dashboard | Staff app shown | ✅ |
| TC-AUTH-02 | P | Admin login | On login screen | Select "Admin", enter creds, Sign In | admin/admin123 | Enters Admin dashboard w/ all data | Admin app, all data | ✅ |
| TC-AUTH-03 | N | Wrong password | — | Login with bad password | user/WRONG | Rejected, stay on login | 401, "Login failed" | ✅ |
| TC-AUTH-04 | N | Role mismatch | — | Staff creds on Admin tab | user/user123 as admin | Rejected | 403 toast | ✅ |
| TC-AUTH-05 | N | Unknown user | — | Login with non-existent user | ghost/x | Rejected | 401 toast | ✅ |
| TC-AUTH-06 | P | Register new user | On register screen | Fill 3-step form, submit | qa_user/testpass123 | "Awaiting Admin approval", status pending | Toast shown, pending | ✅ |
| TC-AUTH-07 | N | Register password mismatch | On register screen | Mismatched passwords | abc/different | Client validation blocks | "Passwords do not match" | ✅ |
| TC-AUTH-08 | E | Session persists on refresh | Logged in | Press F5 / reload | — | Stays in app, no re-login | Stayed in app, role restored | ✅ |
| TC-AUTH-09 | E | No login flash on refresh | Logged in | Reload, observe first paint | — | Login screen never shown; loader shown | Login hidden, "Restoring…" shown | ✅ |
| TC-AUTH-10 | N | Expired/invalid token | Bad token in storage | Reload | garbage token | Falls back to login, clears token | Login shown, token cleared | ✅ |
| TC-AUTH-11 | P | Logout | Logged in | Click "Out" | — | Token cleared, login shown | ✅ | ✅ |

## 2. Purchase Order

| ID | Type | Title | Steps | Test Data | Expected | Actual | Status |
|----|------|-------|-------|-----------|----------|--------|--------|
| TC-PO-01 | P | Create PO | Fill form, Save | PO + qty 300 + warp row | "PO saved", appears in table, persists | Saved & persisted | ✅ |
| TC-PO-02 | N | Missing PO number | Save with blank PO# | qty 100 | Blocked | "PO Number is required" | ✅ |
| TC-PO-03 | N | Order qty = 0 | Save with qty 0 | qty 0 | Blocked | "Order Quantity must be >0" | ✅ |
| TC-PO-04 | N | Duplicate PO number | Create same PO# twice | existing PO# | Rejected | 400 "PO number already exists" | ✅ |
| TC-PO-05 | E | User sees only own POs | Login as 2nd user, open 1st user's PO | — | 403 | 403 | ✅ |
| TC-PO-06 | P | PO yarn feeds dropdowns | Create PO w/ yarn, open Inward | 40s/White | Yarn appears in PO response & dropdowns | warp_rows returned, dropdowns filled | ✅ |

## 3. Inward (cycle guard)

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-IN-01 | P | Create inward | Enter PO, next process, save | Saved, cycle auto = 1 | "Inward saved — Cycle 1" | ✅ |
| TC-IN-02 | E | Cycle auto-increment | After cycle 1 delivered, new inward | Cycle 2 | cycle_number 2 | ✅ |
| TC-IN-03 | N | **Cycle guard** — new inward before prior delivery | 2nd inward, cycle 1 not delivered | Blocked | 400 "previous cycle delivery must be completed" | ✅ |
| TC-IN-04 | P | can-start check | GET can-start cycle 1 / cycle 3 | true / false(reason) | true; false "Cycle 2 not delivered" | ✅ |
| TC-IN-05 | P | Mark inward done | PATCH /inwards/{id}/done | is_done=true | 200 | ✅ |

## 4. Outward & Return

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-OUT-01 | P | Create outward (warping) | Fill form, save | Saved | "Outward saved" | ✅ |
| TC-OUT-02 | P | Mark outward done | PATCH done | 200 | 200 | ✅ |
| TC-RET-01 | P | Create warping return | Add beam entries, save | Saved + beams auto-generated | "Return saved", beams created | ✅ |
| TC-RET-02 | E | Beam IDs globally unique | 2 POs each w/ warping return | No collision | B001..B00n unique across POs | ✅ |

## 5. Loom Allocation (global lock)

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-LOOM-01 | P | Allocate beam→loom | Select beam + free loom, save | Loom occupied | "Loom N allocated", status occupied | ✅ |
| TC-LOOM-02 | E | **Global lock** — occupied loom hidden | After allocation, open loom dropdown | Occupied loom not listed | Dropdown 2–18, loom 1 excluded; free 17 | ✅ |
| TC-LOOM-03 | N | Allocate to occupied loom (API) | POST allocate to occupied loom | Rejected | 400 "Loom is not free" | ✅ |
| TC-LOOM-04 | P | Allocation status PATCH (cancel frees loom) | PATCH status=cancelled | Loom freed | occupied → free | ✅ |

## 6. Manufacturing & Inventory

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-MFG-01 | P | Log daily metres | Save manufacturing | Running total + balance computed | total 250→550, balance 350→50 | ✅ |
| TC-MFG-02 | N | Negative metres | metres_today = -1 | Rejected | 422 | ✅ |
| TC-MFG-03 | P | Mark done → auto-inventory | is_done=true | Allocation completed + inventory created; loom stays occupied | inventory auto-created; loom occupied | ✅ |
| TC-INV-01 | P | Inventory list | GET inventory | Records present | auto-created record present | ✅ |

## 7. Delivery

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-DEL-01 | P | Readiness gate | GET ready before/after weaving | not ready → ready | false (reasons) → true | ✅ |
| TC-DEL-02 | P | Create delivery | Save delivery | DC#, pieces from inventory, loom freed, PO complete | "Delivery saved — DC-000x", loom free, PO complete | ✅ |
| TC-DEL-03 | N | Duplicate delivery (same PO+cycle) | Save twice | Blocked | 400 | ✅ |
| TC-DEL-04 | E | Delivery blocked w/o inventory | Allocations exist, no inventory | Blocked | 400 readiness | ✅ |
| TC-DEL-05 | P | DC slip (admin) | GET dc-slip as admin | Slip JSON | company, customer, pieces, totals | ✅ |

## 8. Admin & Reports

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-ADM-01 | P | Admin sees all data | Login admin | All POs/inwards/etc (not just own) | pos 8, users 3, etc. | ✅ |
| TC-ADM-02 | P | All 7 views render | Click each nav item | Each renders with data | Dashboard/LoomBoard/POs/Warehouse/Mfg/Delivery/Users all OK | ✅ |
| TC-ADM-03 | P | Approve pending user | Approve in User Mgmt | pending → approved | "User approved", status approved | ✅ |
| TC-ADM-04 | P | Update user role | PATCH role | Role changes | 200 | ✅ |
| TC-ADM-05 | N | Invalid role value | PATCH role=super | Rejected | 400 | ✅ |
| TC-ADM-06 | P | CSV export | GET export/csv/pos | text/csv file | 200, header + rows | ✅ |

## 9. Authorization

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-AUTHZ-01 | N | Non-admin → /users | GET /users as staff | 403 | 403 | ✅ |
| TC-AUTHZ-02 | N | Non-admin → /admin/dashboard | as staff | 403 | 403 | ✅ |
| TC-AUTHZ-03 | N | Non-admin → CSV export | as staff | 403 | 403 | ✅ |
| TC-AUTHZ-04 | N | Cross-user record read | user2 GET user1's inward/yarn by id | 403 | 403 | ✅ |
| TC-AUTHZ-05 | N | No token on protected endpoint | GET /pos no auth | 401/403 | 403 | ✅ |

## 10. PO Auto-fill (on entering PO number)

| ID | Type | Title | Steps | Expected | Actual | Status |
|----|------|-------|-------|----------|--------|--------|
| TC-AF-01 | P | Inward auto-fill | Type PO in Inward | Description, cycle, warp/weft count+colour dropdowns populated & single auto-selected | desc, Cycle 1, 40s/White/30s auto-selected | ✅ |
| TC-AF-02 | P | Loom auto-fill | Type PO in Loom Alloc | Description, cycle, beam dropdown (single auto-selected) | beam B007 auto-selected | ✅ |
| TC-AF-03 | P | Delivery auto-fill | Type PO in Delivery | Description, cycle, customer, design no, reed×pick, pieces+totals from inventory | all filled; piece 288 m; design AF3-…, 52×30 | ✅ |
| TC-AF-04 | P | Outward/Return auto-fill | Type PO | Description + cycle | filled | ✅ |

---

## Defect Log (found during testing — all fixed & re-verified)

| DEF | Severity | Found in | Description | Fix | Status |
|-----|----------|----------|-------------|-----|--------|
| DEF-01 | Critical | Login | Admin login was a hardcoded `admin/admin` bypass → no token → empty admin dashboard | Route admin through the API | ✅ Fixed |
| DEF-02 | Critical | PO create | Empty optional date fields sent as `""` → 422 | Send `null` for empty fields | ✅ Fixed |
| DEF-03 | Critical | Return | `beam_number` global-unique collision → 2nd PO warping return 500 | Global beam sequence + retry | ✅ Fixed |
| DEF-04 | High | Delivery | `clearDeliveryForm` null `.textContent` → success showed error toast | Null-guard nodes | ✅ Fixed |
| DEF-05 | Medium | Manufacturing | Toast said "Loom freed" (loom frees at delivery); inventory not reloaded | Corrected toast + reload | ✅ Fixed |
| DEF-06 | High | Session | Refresh logged the user out | Restore session from JWT on load | ✅ Fixed |
| DEF-07 | Low | Session | Login screen flashed before dashboard on refresh | Hide login pre-paint + loader | ✅ Fixed |
| DEF-08 | High | Auto-fill | PO response omitted yarn rows → dropdowns empty | Attach warp/weft rows to PO responses | ✅ Fixed |

## Environment / Notes
- Render free backend cold-starts (~50s) after 15 min idle — first request after idle is slow (not a defect).
- Free Postgres expires 2026-06-30.
- DC numbers are server-generated and unique per PO+cycle.

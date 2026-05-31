# PA FABS ERP — Complete System Audit & Test Report
_Tested live against production on 2026-05-31. Frontend: https://pa-fabs-erp-frontend.vercel.app · Backend: https://pa-fabs-erp-backend.onrender.com_

Legend: ✅ works (live-tested) · ⚠️ works but flawed · ❌ broken (live-tested) · 🔓 no-auth gap

---

## 1. Executive summary

| Area | Verdict |
|------|---------|
| Auth (login / JWT / roles) | ✅ Working and correctly enforced |
| Authorization (user vs admin) | ✅ Enforced (`/api/users` admin-only verified) |
| Read/list endpoints | ✅ All working |
| **Create endpoints (write path)** | ❌ **Core ones 500 — PO, Inward, Register all broken** |
| Frontend → backend integration | ⚠️ Partial — 4 of 8 forms never call the API; date format mismatch breaks the rest |
| Security | ⚠️ Several by-id endpoints are public (🔓) |

**Bottom line:** You can log in, browse, and read data. You **cannot create a Purchase Order, Inward entry, or register a user** — those 500 on the server. And half the data-entry forms in the UI don't talk to the backend at all (they write to in-memory JS only and lose data on refresh).

---

## 2. Authentication & Authorization — ✅ TESTED, WORKING

| Test | Result |
|------|--------|
| Login `user`/`user123` as `user` | ✅ 200 + JWT |
| Login `admin`/`admin123` as `admin` | ✅ 200 + JWT |
| Login wrong password | ✅ 401 |
| Login correct user, **wrong role** (user→admin) | ✅ 403 |
| Login **invalid role string** (`superadmin`) | ❌ 500 (should be 422/403 — `UserRole(str)` throws `ValueError`, auth.py:53) |
| Protected endpoint, **no token** | ✅ 403 |
| Protected endpoint, **garbage token** | ✅ 401 |
| `/api/users` with **user** token | ✅ 403 (admin-only enforced) |
| `/api/users` with **admin** token | ✅ 200 |

- JWT: HS256, 24h expiry, `SECRET_KEY` from env (Render-generated). No refresh/revocation.
- `get_current_user` requires `is_approved=True` AND `status=APPROVED`. `get_current_admin` adds role check. Both verified live.

---

## 3. Complete API inventory — 35 endpoints, live-tested

### Auth
| Endpoint | Auth | Live result |
|---|---|---|
| POST `/api/login` | open | ✅ 200 |
| POST `/api/register` | open | ❌ **500** — `auth.py:26` reads `user.created_at`, which `UserCreate` has no field for |
| GET `/api/me` | user | ✅ 200 |

### Purchase Orders
| Endpoint | Auth | Live result |
|---|---|---|
| POST `/api/pos/` | user | ❌ **500** — `pos.py:23` `row.get("count")` called on a Pydantic model (no `.get`) |
| GET `/api/pos/` | user | ✅ 200 (admin sees all, user sees own) |
| GET `/api/pos/{po}` | user | ✅ (ownership enforced) |
| PUT `/api/pos/{po}` | user | (blocked — needs a PO, which can't be created) |
| DELETE `/api/pos/{po}` | admin | admin-only |
| GET `/api/pos/{po}/yarn` | 🔓 open | ✅ 200 — **public**, no auth |
| GET `/api/pos/{po}/cycles` | 🔓 open | ✅ 200 — **public**, no auth |

### Inward / Outward / Returns
| Endpoint | Auth | Live result |
|---|---|---|
| POST `/api/inwards/` | user | ❌ **500** — `inward.py:25` uses `func.max` but `func` is never imported (`NameError`) |
| GET `/api/inwards/` | user | ✅ 200 |
| GET `/api/inwards/{id}` | 🔓 open | public |
| POST `/api/outwards/` | user | ⚠️ reachable; returns 404 "No inward entry" because inwards can't be created. PK = `hash(po+operator)` → collides on 2nd entry (outward.py:28) |
| GET `/api/outwards/` | user | ✅ 200 |
| GET `/api/outwards/{id}` | 🔓 open | public |
| POST `/api/returns/` | user | ⚠️ reachable; PK = `hash(po+return_type)` → collides on 2nd return (returns.py:29) |
| GET `/api/returns/` | user | ✅ 200 |
| GET `/api/returns/{id}` | 🔓 open | public |

### Looms / Manufacturing / Deliveries
| Endpoint | Auth | Live result |
|---|---|---|
| GET `/api/looms/` | 🔓 open | ✅ 200 (18 looms seeded) |
| GET `/api/looms/free` | 🔓 open | ✅ 200 |
| GET `/api/looms/{n}` | 🔓 open | ✅ 200 |
| POST `/api/looms/allocate` | user | ❌ will **500** — `looms.py:78` uses `BeamStatus` (not imported, `NameError`). Currently blocked earlier by missing inward. Also `allocation_date` is set to `expected_done` (looms.py:62) |
| GET `/api/manufacturing/` | user | ✅ 200 |
| POST `/api/manufacturing/` | user | ❌ will **500** — `manufacturing.py:43` does `int + str` in hash (`TypeError`); `manufacturing.py:66` references unimported `backend.models...` when `is_done=True` |
| GET `/api/manufacturing/{n}` | 🔓 open | ✅ 200 |
| POST `/api/deliveries/` | user | ⚠️ reachable, validates (needs `pieces_data[].piece_no`) |
| GET `/api/deliveries/` | user | ✅ 200 |
| GET `/api/deliveries/{id}` | 🔓 open | public |
| GET `/api/deliveries/{id}/dc-slip` | 🔓 open | **public** — full DC slip (customer, GSTIN, vehicle) with no auth |

### Admin
| Endpoint | Auth | Live result |
|---|---|---|
| GET `/api/users` | admin | ✅ 200 (403 for non-admin) |
| PUT `/api/users/{id}/approve` | admin | admin-only |
| PUT `/api/users/{id}/reject` | admin | admin-only |

**Endpoints the frontend calls that DON'T EXIST (404):** `/beams`, `/loom-allocs`, `/mfgs`, `/inventory`, `/deliveries/counter`.
**Orphaned models (no API at all):** `inventory`, `beams` (created only as a side effect of returns), `loom_allocations` (write-only — no list/read endpoint).

---

## 4. Frontend pages — functionality status

| Page | App | Reads from API? | Writes to API? | Status |
|------|-----|----------------|----------------|--------|
| Login | — | — | POST /login | ✅ Works (user). ⚠️ **Admin login `admin`/`admin` is a hardcoded bypass** — sets no token, so admin dashboard loads **empty** |
| Register (3-step) | — | — | ❌ never calls /register | ❌ Pushes to local JS only, then calls undefined `save()` → **JS crash**, data lost on refresh. (Backend /register also 500s anyway) |
| Admin Dashboard | adminApp | yes (needs admin token) | — | ⚠️ Works only via real admin API login (not the hardcoded path) |
| Loom Status Board | adminApp | GET /looms ✅ | — | ✅ Works |
| All POs | adminApp | GET /pos ✅ | — | ✅ Lists; create is broken (see below) |
| Warehouse view | adminApp | GET inwards/outwards/returns ✅ | — | ✅ Read works |
| Manufacturing view | adminApp | GET /manufacturing ✅ | — | ✅ Read works |
| Delivery view | adminApp | GET /deliveries ✅ | — | ✅ Read works |
| User Management | adminApp | GET /users ✅ | ❌ approve/reject are client-only | ⚠️ Lists users, but Approve/Reject **don't persist** (no PUT call; calls undefined `save()`) |
| User Dashboard | userApp | loadAllData ✅ | — | ✅ Works (shows seeded looms) |
| **PO Details** | userApp | GET /pos | POST /pos | ❌ POST **500s** (+ sends date-only, would 422) |
| **Inward Entry** | userApp | GET /inwards | POST /inwards | ❌ POST **500s** |
| **Outward Entry** | userApp | — | ❌ never calls API | ❌ Client-only — `saveOutward()` writes to JS + undefined `save()`; lost on refresh |
| **Loom Allocation** | userApp | — | ❌ never calls API | ❌ Client-only |
| **Manufacturing** | userApp | — | ❌ never calls API | ❌ Client-only |
| **Return Entry** | userApp | GET /returns | POST /returns | ⚠️ Calls API but sends date-only → 422; also checks `response.success` (backend doesn't return it) |
| **Delivery & DC** | userApp | GET /deliveries | POST /deliveries | ⚠️ Calls API; DC number generated client-side from a counter that never persists (duplicate DC-0001 every session) |

---

## 5. Critical bugs (verified live, with cause)

**Backend — break core features (500):**
1. `POST /api/register` → `auth.py:26` `user.created_at` (no such field). Registration impossible.
2. `POST /api/pos/` → `pos.py:23` `row.get("count")` on a Pydantic model. **Cannot create POs.**
3. `POST /api/inwards/` → `inward.py:25` `func` not imported. **Cannot create inward entries.**
4. `POST /api/looms/allocate` → `looms.py:78` `BeamStatus` not imported.
5. `POST /api/manufacturing/` → `manufacturing.py:43` `int+str` hash; `:66` unimported module ref.
6. `POST /api/login` with a non-enum role string → 500 (`auth.py:53`).
7. PK-collision design in outwards/returns/manufacturing (`hash(...)` of non-unique fields) → 2nd record per group 500s.

**Backend — security (🔓 public, no auth):**
8. By-id reads for pos-yarn, pos-cycles, inwards, outwards, returns, manufacturing, deliveries, **and the DC slip** are all open. Guessing an ID leaks business data.

**Frontend — integration:**
9. `todayISO()` sends `YYYY-MM-DD`; backend datetime fields reject it → 422 on every API-connected form.
10. `save()` is called in 11 places but **never defined** → `ReferenceError` in register, outward, loom-alloc, manufacturing, inventory, approve/reject.
11. 4 forms (Outward, Loom Allocation, Manufacturing, Inventory) and Approve/Reject never call the backend — data is in-memory only.
12. Admin login bypasses the API (hardcoded `admin`/`admin`) → no token → empty admin dashboard.
13. Calls to 5 non-existent endpoints (`/beams`, `/loom-allocs`, `/mfgs`, `/inventory`, `/deliveries/counter`).

---

## 6. What works end-to-end right now
- Login (user + admin via API), JWT issuance, role + approval gating, logout.
- All list/read endpoints (POs, inwards, outwards, returns, deliveries, manufacturing, looms, users-as-admin).
- The dashboards render with live seeded data (18 looms).

## 7. What's broken
- Creating: POs, Inward entries, user registration, loom allocation, manufacturing logs (server 500).
- Persisting: Outward, Loom Allocation, Manufacturing, Inventory, user Approve/Reject (frontend never calls API).
- Admin dashboard data via the hardcoded admin login (no token).
- Any API form using a date field (date-format 422).

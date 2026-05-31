# PA FABS ERP — Backend Completion Plan
_Tracking the gap between Documentation v2.0 and the current backend. Backend-first._

Status legend: ✅ done · 🟡 partial · ❌ missing

## Module status vs spec

| Module | Spec endpoints | Status |
|--------|---------------|--------|
| Auth | register, login, me | ✅ (login/register/me work) |
| Admin users | list, approve, reject, **role update** | 🟡 list/approve/reject done; role-update ❌; should be PATCH |
| PO | list, create, get, update, cycles, **timeline**, yarn | 🟡 timeline ❌; admin/own scoping ✅ |
| Inward | create, list, get, **po/{po}**, **po/{po}/cycle/{n}**, **{id}/done**, **can-start** | 🟡 create/list/get done; filters + done + can-start ❌ |
| Outward | create, list, get, **po/{po}/cycle/{n}**, **{id}/done** | 🟡 filters + done ❌ |
| Return | create, list, get, **po/{po}/cycle/{n}** | 🟡 cycle filter ❌; needs outward_id FK link |
| Beams | list, **available**, **po/{po}/cycle/{n}**, get | 🟡 list/get done; available(have /free), cycle filter ❌ |
| Loom allocation | create, list, **looms/free**, **looms/status board**, **po/{po}/cycle/{n}**, get/{id}, **{id}/status** | 🟡 create/list/free done; status-board, cycle filter, get, status-patch ❌ |
| Manufacturing | create, list, **po/{po}/cycle/{n}**, loom/{n}, **{id}/done** | 🟡 create/list/by-loom done; cycle filter + done ❌ |
| **Inventory Inward** | create, list, **po/{po}/cycle/{n}** | ❌ **entire module missing** (model+schema exist, no router) |
| Delivery | **ready check**, create, list, get, **po/{po}**, slip | 🟡 create/list/get/slip done; readiness + auto-build pieces from inventory + po-list ❌ |
| Admin/Reports | dashboard, warehouse, manufacturing, delivery, looms, **export csv**, po report | ❌ **all missing** |

## Core business rules to enforce (currently weak/absent)
1. **Cycle guard** — block new inward if previous cycle has no delivery. (inward.py has partial logic; expose `can-start` + verify.)
2. **Global loom lock** — loom freed ONLY on delivery save (✅ already), only free looms in dropdown (✅). Add status board endpoint.
3. **Delivery readiness** — all allocations completed + inventory exists; pieces_data auto-built from inventory_inward (❌ currently manual).
4. **Permissions matrix** — delivery=user-only; dashboards/export/dc-slip=admin-only; role update=admin (❌ several gaps).

## Phases (each ends with a code review + tests)
- **P1** Inventory Inward module + wire delivery to it (readiness + auto pieces). 
- **P2** Cycle-aware GET filters + PATCH `/done` endpoints (inward/outward/manufacturing) + inward `can-start`.
- **P3** Loom-allocation completion: status board, by-cycle, get-by-id, status patch.
- **P4** Admin module: dashboard, warehouse, manufacturing, delivery, looms views + CSV export + PO report/timeline.
- **P5** Permissions alignment to the role matrix + user role-update endpoint.
- **P6** Code-quality sweep: enum comparisons (not strings), timezone-aware datetimes, consistent error handling, remove dead code, docstrings, query-filter helpers.

## Code-quality standards being applied
- Compare enums to enum members, not string literals.
- `datetime.now(timezone.utc)` not `utcnow()`.
- UUID PKs everywhere (done).
- Ownership/role checks via shared deps.
- Pydantic response models parse JSON columns (delivery pieces ✅).

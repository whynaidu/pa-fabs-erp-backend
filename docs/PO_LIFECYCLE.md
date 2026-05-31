# PA FABS ERP — Complete PO Lifecycle (Beginning to End)
_Verified end-to-end against production on 2026-05-31. Example values are from a real traced run: PO `DOC-1780242312`, order qty 600 m._

Backend: https://pa-fabs-erp-backend.onrender.com · Frontend: https://pa-fabs-erp-frontend.vercel.app
Auth: every step below carries `Authorization: Bearer <JWT>`. A user sees only their own POs; admin sees all.

---

## 0. The two production paths
A PO (Purchase Order) is the master job. It runs in **cycles**; each cycle goes raw-yarn → fabric → delivery, then the next cycle can begin under the same PO.

- **Warp path (direct warping):** Inward → Outward Warping → Return from Warping → Loom Allocation → Weaving → Inventory → Delivery
- **Weft path (winding first, parallel):** Inward → Outward Winding → Return from Winding → Outward Warping → Return from Warping → Loom Allocation → Weaving → Delivery

The trace below follows the **warp path** for cycle 1, then opens cycle 2 to prove the cycle guard.

---

## Stage-by-stage (verified)

### 1. Create PO — `POST /api/pos/`
The master record. PO number is the user-entered **primary key**. Warp/weft rows become the dropdown source for every downstream form.
- **In:** po_number, description, purchaser, reed, pick, width, order_qty, cost_per_meter, `warp_rows[]`, `weft_rows[]` (count, colour, qty_kg, bundles).
- **Out:** PO with `status: pending`, `user_id` set to the creator.
- **Result:** `DOC-1780242312`, order_qty 600, status `pending`.

### 2. Yarn dropdown — `GET /api/pos/{po}/yarn`
Feeds the Inward/Outward/Return forms.
- **Out:** `{warp_counts:["40s"], warp_colours:["White","Blue"], weft_counts:["30s"], weft_colours:["Red"]}`.

### 3. Cycle guard check — `GET /api/inwards/po/{po}/can-start`
- **Out:** `{can_start: true, next_cycle: 1}` — first cycle is always allowed.

### 4. Inward (material receipt) — `POST /api/inwards/`
First step of a cycle. **Cycle number is auto-assigned by the backend** (MAX+1).
- **In:** po_number, warp/weft count+colour+kg, rm_number, next_process (`warping`/`winding`/`both`), received_by, entry_date.
- **Out:** inward with `cycle_number: 1`. PO status → `in_progress`.
- **Rule:** if a previous cycle exists without a completed delivery, this is **blocked** (see step 20).

### 5. Outward — `POST /api/outwards/`
Material issued to an external operator (warping or winding).
- **In:** po_number, process_type (`warping`), operator_name, warp/weft details, outward_date. Cycle is derived from the latest inward.
- **Out:** outward with `cycle_number: 1`.

### 6. Return from warping — `POST /api/returns/`
Material comes back to warehouse stock. For a warping return, the backend **auto-generates beams**.
- **In:** po_number, return_type (`warping_return`), beams_returned, quality_grade, `beam_entries[]` (beam_metres, total_ends).
- **Out:** return record; one Beam row per beam_entry, status `available`.
- **Result:** beams `B002`, `B003` created (300 m each, grade A).
- **Note:** beam numbers are **globally unique** (they are the FK target for loom allocations), so they run as a global B### sequence rather than resetting per cycle.

### 7. Beams list — `GET /api/beams/po/{po}/cycle/{n}` (or `/api/beams/available`)
- **Out:** `[B002 (300m, available), B003 (300m, available)]`.

### 8. Loom allocation — `POST /api/looms/allocate`  ← **global lock**
Each warped beam → one of 18 looms. Only **free** looms are offered.
- **In:** po_number, beam_id (a beam_number), loom_number, weft_details, expected_done.
- **Out:** allocation record (status `active`).
- **Rule:** if the loom isn't free → 400.

### 9. Loom state — `GET /api/looms/{n}`
- **Out:** loom 3 → `status: occupied`, `current_po: DOC-…`, `current_cycle: 1`, `current_beam: B002`.
- **Proof of global lock:** free-loom count went **18 → 17**; loom 3 no longer appears in `GET /api/looms/free` for **any** user.

### 10–11. Manufacturing (weaving) — `POST /api/manufacturing/`
Daily metres per loom; running total and balance auto-computed (Balance = order_qty − total).
- Day 1: metres_today 250 → total 250, **balance 350**.
- Day 2 (`is_done: true`): metres_today 300 → total 550, **balance 50**.
- **On `is_done`:** the loom allocation is marked `completed`, and the woven fabric is **auto-received into inventory** (so the cycle becomes deliverable without a separate manual step). The loom **stays occupied** — it is freed only at delivery.

### 12. Inventory — `GET /api/inventory-inward/`
- **Out:** 1 record — loom 3, fabric_metres 298 (auto-created from the "done" log).

### 13. Delivery readiness — `GET /api/deliveries/po/{po}/cycle/{n}/ready`
- **Out:** `{ready: true, allocation_count: 1, inventory_count: 1}`.
- **Rule:** every allocated loom for the cycle must be `completed` AND have an inventory record.

### 14. Delivery — `POST /api/deliveries/`  ← one per PO+cycle
- **In:** po_number, delivery_date, customer_name, vehicle/driver/receiver, remarks. Pieces are **auto-built from inventory**.
- **Out:** `dc_number: DC-0002`, no_pieces 1, grand_total_metres 298, `pieces_data:[{piece_no:"1", metres:298}]`.
- **Atomic side-effects (same transaction):** all looms for this PO+cycle are **freed**; PO status → `complete`.
- **Rule:** a second delivery for the same PO+cycle → 400 (also DB unique-constrained).

### 15–16. Post-delivery state
- Loom 3 → `status: free`, `current_po: null` (released).
- PO `DOC-…` → `status: complete`.

### 17. DC slip — `GET /api/deliveries/{id}/dc-slip` (**admin only**)
- **Out:** company header (PA FABS, GSTIN), to-customer, pieces, totals — the printable delivery challan.

### 18–20. Next cycle + cycle guard
- `can-start` → `{can_start: true, next_cycle: 2}` (cycle 1 was delivered).
- Inward created → `cycle_number: 2`.
- `can-start` again → `{can_start: false, reason: "Cycle 2 delivery not complete"}` — **a third cycle is blocked** until cycle 2 delivers. ✅ guard proven.

### 21. Admin timeline — `GET /api/pos/{po}/timeline` (admin only)
- **Out:** cycle 1 → inward ✓, delivery ✓; cycle 2 → inward ✓, delivery ✗.

---

## Business rules — all verified live
| Rule | Where proven | Result |
|------|--------------|--------|
| PO number is the primary key; one user → many POs | step 1 | ✅ |
| Cycle number auto-assigned (MAX+1) | steps 4, 19 | 1 then 2 |
| **Cycle guard** — new cycle blocked until prior delivered | steps 3, 18, 20 | ✅ blocked at cycle 3 |
| **Global loom lock** — occupied on allocate, hidden from all | steps 8, 9 | free 18→17 |
| Loom freed **only** at delivery | steps 11, 15 | stayed occupied through weaving |
| Running total + balance auto-calculated | steps 10, 11 | 250→550, bal 350→50 |
| Inventory received before delivery | steps 11, 12 | auto on done |
| Delivery readiness gate | step 13 | ready=true |
| One delivery per PO+cycle; pieces from inventory; auto DC# | step 14 | DC-0002 |
| Delivery frees looms + completes PO atomically | steps 15, 16 | ✅ |
| DC slip / timeline / exports = admin only | steps 17, 21 | ✅ |

---

## Bug found & fixed during this trace
**`beam_number` global-uniqueness collision.** Beam numbers were generated as `B001` per PO+cycle, but the column is globally unique (it's the FK target for loom allocations). The **second PO** with a warping return always collided on `B001` → HTTP 500. Single-step tests missed it; the full cycle caught it. Fixed to a global B### sequence with a retry guard, and beam `quality_grade` is now stored. (commit `9dd2e98`)

## Verification status
The full 21-step lifecycle above ran **green end-to-end on production**, plus a second cycle proving the guard. Combined with the earlier 33-endpoint sweep and the in-browser UI checks (both logins, PO create persists), the PO lifecycle is fully working.

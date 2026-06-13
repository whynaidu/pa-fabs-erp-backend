# PA FABS ERP — Client Change Requests (Tuesday call)
Status: 🔲 todo · 🟡 in progress · ✅ done · ❓ needs client input

_Decisions: Q1 warp qty = PO qty × (1+shortage%) [2400@8%=2592]; Q2 dropdown Table/Loom; Q3 delivery on manufactured fabric; Q4 mfg total per PO+cycle._

## A. User page — PO Details
- 🟡 Specifications: **"On Table / On Loom"** dropdown after Reed and Pick — backend ✅, frontend pending
- 🔲 Remove Warp rows & Weft rows from PO; move them to **Inward Entry** (P2)
- 🟡 After "Cost per Metre" add **Warp Count, Weft Count, Total Ends** — backend ✅, frontend pending
- 🔲 Rename "Order Quantity (metres)" → **"Purchase Order Quantity (metres)"** (frontend)
- 🟡 **Shortage %** field — backend ✅, frontend pending
- 🟡 **Total Warp Quantity (metres)** = qty×(1+shortage%) — backend computes ✅ (verified 2400→2592), frontend pending

## B. User page — Inward Entry
- 🔲 Remove **Next Process** tab/field
- 🔲 Replace warp/weft detail fields with **Warp rows & Weft rows** (moved from PO)
- 🔲 Add **Location** column

## C. User page — Outward Entry
- 🔲 Winding process → show **both** warp-rows and weft-rows blocks
- 🔲 Add **Weaving** option to Process Type → shows **weft-rows block only** (no warp)

## D. User page — Return Entry
- 🔲 Warping return: **Total Ends** auto-fills from the PO specification

## E. User page — Manufacturing
- 🔲 Remove the **Inward Entry block** (frontend)
- ✅ Fix calculation — now per PO+cycle (backend)

## F. User page — Delivery
- ✅ Delivery depends on **manufactured metres only** (backend — verified)
- 🟡 Pieces table **No / Metres / Weight (kg)** + footer totals — backend accepts weight + total_weight ✅, frontend pending

## Backend status (P1) — DEPLOYED ✅
mfg per-cycle calc · delivery manufactured-gate + weight · PO shortage%/total_warp/counts/ends/table-loom · outward weaving · inward location · live-DB column+enum migration · beam numbering MAX-based (fixed 409).

## G. Admin page
- 🔲 **View / Edit / Delete** on every stage (PO, inward, outward, return, loom, mfg, inventory, delivery)
- 🔲 **Download** option per stage
- 🔲 Tables not showing fully → fix layout/overflow

## H. UI — global
- 🔲 Login page: add weaving-machine / Lord Murugan image on the left panel
- 🔲 Logo: icon only (no background, no letters)
- 🟡 New registration error → trace frontend register form (backend confirmed OK)

## I. UI — User page
- 🔲 Attractive icons for all tabs
- 🔲 **Pagination** on all detail tables
- 🔲 Fix null/undefined values shown in tables
- 🔲 User gets **Search + View** only (no edit/delete)
- 🔲 Delivery & DC: **Print** shows only that one delivery challan

## Open questions (blocking)
- **Q1** Total Warp Quantity formula — the example (2400 m, 8% → 300 m) is mathematically inconsistent.
- **Q2** "On Table / On Loom" — a dropdown choice, or two separate value columns?
- **Q3** Delivery rule — drop the inventory/all-looms gate and allow delivery whenever fabric is manufactured?
- **Q4** Manufacturing total — confirm it should be per PO+cycle (not per loom across allocations).

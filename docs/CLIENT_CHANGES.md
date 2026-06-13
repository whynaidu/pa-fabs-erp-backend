# PA FABS ERP — Client Change Requests (Tuesday call)
Status: 🔲 todo · 🟡 in progress · ✅ done · ❓ needs client input

## A. User page — PO Details
- 🔲 Specifications: add **"On Table / On Loom"** indicator after Reed and after Pick ❓(field shape — see Q2)
- 🔲 Remove Warp rows & Weft rows from PO; move them to **Inward Entry**
- 🔲 After "Cost per Metre" add columns: **Warp Count, Weft Count, Total Ends**
- 🔲 Order details: rename "Order Quantity (metres)" → **"Purchase Order Quantity (metres)"**
- 🔲 Add **Shortage %** field (e.g. 8%)
- 🔲 Add **Total Warp Quantity (metres)** — auto-calculated from PO Qty + Shortage % ❓(formula — see Q1)

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
- 🔲 Remove the **Inward Entry block**
- 🟡 Fix calculation — running total bleeds across allocations on the same loom (should be per PO+cycle) ❓(confirm — Q4)

## F. User page — Delivery
- 🔲 Delivery depends on **manufactured metres only**, not loom-free / all-looms-complete ❓(confirm — Q3)
- 🔲 Pieces table columns: **No, Metres, Weight (kg)**; footer totals: **Total pieces, Total metres, Total weight**

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

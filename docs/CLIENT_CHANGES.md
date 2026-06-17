# PA FABS ERP — Client Change Requests (Tuesday call)
Status: 🔲 todo · 🟡 in progress · ✅ done · ❓ needs client input

_Decisions: Q1 warp qty = PO qty × (1+shortage%) [2400@8%=2592]; Q2 dropdown Table/Loom; Q3 delivery on manufactured fabric; Q4 mfg total per PO+cycle._

## A. User page — PO Details
- ✅ Specifications: **"On Table / On Loom"** dropdown after Reed and Pick
- ✅ Remove Warp rows & Weft rows from PO; moved to **Inward Entry**
- ✅ After "Cost per Metre" add **Warp Count, Weft Count, Total Ends**
- ✅ Rename "Order Quantity (metres)" → **"Purchase Order Quantity (metres)"**
- ✅ **Shortage %** field
- ✅ **Total Warp Quantity (metres)** = qty×(1+shortage%) — verified 2400→2592, auto-calc live

## B. User page — Inward Entry
- ✅ Remove **Next Process** tab/field
- ✅ Replace warp/weft detail fields with **Warp rows & Weft rows** (moved from PO, pre-filled + editable) — backend+frontend, verified live
- ✅ Add **Location** column

## C. User page — Outward Entry
- ✅ Winding process → show **both** warp-rows and weft-rows blocks
- ✅ Add **Weaving** option to Process Type → shows **weft-rows block only** (no warp)

## D. User page — Return Entry
- ✅ Warping return: **Total Ends** auto-fills from the PO specification (beam rows)

## E. User page — Manufacturing
- ✅ Remove the **Inward Entry block** (frontend; fabric received automatically = metres produced)
- ✅ Fix calculation — now per PO+cycle (backend)

## F. User page — Delivery
- ✅ Delivery depends on **manufactured metres only** (backend — verified)
- ✅ Pieces table **No / Metres / Weight (kg)** + live footer totals; total weight in tables + DC slip

## Backend status (P1) — DEPLOYED ✅
mfg per-cycle calc · delivery manufactured-gate + weight · PO shortage%/total_warp/counts/ends/table-loom · outward weaving · inward location · live-DB column+enum migration · beam numbering MAX-based (fixed 409).

## G. Admin page
- ✅ **View / Edit / Delete** on every stage (PO, inward, outward, return, mfg, delivery, loom-alloc). Whitelisted PUT endpoints (admin-only) + generic pre-filled edit modal; DELETE endpoints with FK cascades. Verified live (edit saves, derived state preserved, non-admin → 403).
- ✅ **Download** (CSV) per stage (inward/outward/return/mfg/delivery/PO)
- ✅ Tables not showing fully → fixed (table-card overflow-x auto + nowrap headers)
- ✅ Bonus fixes: staff `/users` 403 noise removed; login role-desync after logout fixed (was causing "Role mismatch").

## H. UI — global
- ✅ Login page: weaving / Lord Murugan art hook on left panel (drop `login_art.jpg` in frontend root; dark-scrim overlay, gradient fallback)
- ✅ Logo: icon only (transparent, no box/border/letters)
- ✅ New registration error fixed — frontend sent job-title as `role` (enum only allows user/admin → 422); now sends role=user, job title → department. Verified 200/pending live.

## I. UI — User page
- ✅ Attractive icons for all tabs (line-SVG icons already per tab)
- ✅ **Pagination** on all detail tables (generic paginateTable, 10/page)
- ✅ Fix null/undefined values in tables (nz() null-safe helper across unit cells)
- ✅ User is **Search + View** only — user pages expose no edit/delete (admin-only)
- ✅ Delivery & DC: **Print** shows only that one challan (isolated print window)

## Decisions (resolved)
- **Q1** Total Warp = PO qty × (1 + shortage%) → 2400@8% = 2592. ✅
- **Q2** "On Table / On Loom" = dropdown. ✅
- **Q3** Delivery gated on manufactured fabric only. ✅
- **Q4** Manufacturing total per PO+cycle. ✅

## ALL CLIENT CHANGES (A–I) COMPLETE ✅ — deployed to Render (backend) + Vercel (frontend)

## Round 2 — "PA Fabs points.docx" feedback (8 points) — ALL DONE ✅ (verified live)
1. ✅ Inward Warp/Weft row **Count** seeds from PO's Warp Count / Weft Count (rows were moved off PO).
2. ✅ Outward + winding-return + loom-alloc Count/Colour **dropdowns source from the latest Inward entry** (was reading the now-empty PO rows). Verified: warp count "40s" appears from inward.
3a. ✅ Warping return **Total Ends auto-fills from PO** — a beam row is seeded on type-select and refreshed on PO change. Verified 4000 shown for a PO with total_ends.
3b. ✅ Winding return now has a **Warp Rows** block too (was weft-only).
4. ✅ Manufacturing **PO# / Description** now show on loom-select — fixed a camelCase bug (`current_po` → `currentPo`, code read `currentPO`). Order Qty/Balance now correct.
5. ✅ All stage lists return **newest-first** (`order_by created_at desc` on pos/inward/outward/return/inventory; mfg/delivery/alloc already desc). Verified.
6. ✅ Sidebar shows the **logged-in user's real name** + dept + initial (was hardcoded "Staff User"). Verified "Demo Staff User".
7. ✅ Return **422 fixed** — `BeamEntry.total_ends` now Optional (PO-derived) and a frontend guard requires Beam Metres > 0 (clear message vs raw 422). Verified 200.
8. ✅ Admin Return **delete 500/"failed to fetch" fixed** — `flush()` between allocation/beam/return deletes (FK ordering). Verified 200.

## Round 3 — follow-up feedback (5 points) — ALL DONE ✅ (verified)
1. ✅ Admin **User Management → Delete user** (DELETE /users/{id}; guards self + default admin) + 🔑 reset-password action. Verified 200 / non-admin 403.
2. ✅ **Forgot password** on login — "Forgot password?" → reset screen; POST /forgot-password verifies username+email then sets new password. Verified reset+login 200, wrong email 404. (+ admin reset PATCH /users/{id}/password.)
3. ✅ **DC slip print == preview** — one `dcSlipMarkup()` builder for preview + saved-DC view + print; print injects the app stylesheet. Verified saved view renders full challan layout.
4. ✅ **Loom stays assigned until full production** — partial/batch deliveries no longer free the loom; the loom is released and PO marked complete only when total manufactured ≥ order_qty. Multiple batch deliveries per PO+cycle now allowed (dropped uq_delivery_po_cycle + readiness "already exists" gate). Verified: partial→loom occupied, 2nd batch 200, full→loom freed.
5. ✅ **Attractive emoji icons** for all user + admin nav tabs (replaced faint line-SVGs). Verified live.

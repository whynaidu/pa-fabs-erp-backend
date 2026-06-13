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

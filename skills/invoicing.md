---
name: invoicing
description: Rules and workflow for creating invoices from unbilled time. Use whenever the user asks to invoice a client, bill for work, or asks what's ready to invoice.
---

# Invoicing

## Rules

1. An invoice draws **only unbilled time** for **one client**. The same hour can never appear
   on two invoices — the tool marks entries billed and stamps them with the invoice id
   atomically. This is the reason the tool exists; never assemble an invoice by hand.
2. Invoice ids are `INV-<year>-<seq>`, sequential within the year. The tool assigns them.
3. Rates come from the **project**, not typed in at invoice time. If the user wants a
   different rate, the project record changes first (and only affects unbilled entries).
4. New invoices are created in `draft` status. Moving to `sent` and `paid` is a data edit the
   user asks for explicitly; validate after.
5. Before invoicing, show the user what would be drawn: `python tools/report.py unbilled`.
   No surprises on totals.

## Workflow

```
python tools/report.py unbilled                       # 1. show what's ready
python tools/make_invoice.py --client CL-001 --date 2026-07-04   # 2. create it
python tools/validate.py                              # 3. confirm integrity
```

The tool refuses a client with no unbilled time. After invoicing, regenerate the dashboard if
it exists (`python views/build_dashboard.py`) so the unbilled numbers on screen match the data.

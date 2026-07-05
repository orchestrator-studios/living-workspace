# System Overview

*Filled in by interview, 2026-07-04. Everything else in this workspace traces back to this file.*

## Purpose

Track a solo consulting practice end to end: who the clients are, what projects are running at
what rates, where the billable time goes, and what has and hasn't been invoiced — so that
monthly invoicing is mechanical and nothing billable is ever lost or double-billed.

## The things

- **Client** — an organization that hires the practice; has a primary contact.
- **Project** — one engagement for one client, billed hourly at a project-specific rate.
- **Time entry** — a block of work on one project on one date, with a note a client could read.
- **Invoice** — a monthly bill to one client, drawing that client's unbilled time.

## The rules

- Time is billed in **quarter-hour increments**; smallest entry 0.25h.
- **Rates belong to projects**, not clients — one client can run two projects at two rates.
- Once a time entry is on an invoice it is **frozen** — never edited, never re-billed.
- An invoice draws **only unbilled time**, for **one client**. The same hour can never appear
  on two invoices.

## Where the data lives today

One **Google Drive folder per client**, each containing the engagement letter (contacts,
projects, rates, start dates) and a running **time-log sheet** (date, project, hours, notes).
Nothing else — no invoicing has happened yet this cycle.

## What you'll ask of it

- "Log two and a half hours on vendor selection for Wednesday — scoring session."
- "What's unbilled, by client?"
- "Invoice Meridian for everything outstanding."
- A glanceable view: unbilled by client, recent time — without having to ask.

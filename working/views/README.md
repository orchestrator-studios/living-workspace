# views/ — view logic (templates)

This folder holds the **presentation logic** for views: the templates. It does **not** hold rendered
output.

A view has three separable parts, kept in three places:

| Part | Lives in |
|---|---|
| **Code** — reads data, computes, binds | `tools/` (`build_report.py`, `build_views.py`) |
| **Template** — the presentation markup with placeholders | **here**, `views/` (`report.template.html`) |
| **Instance** — one study's rendered output | that study's folder, `data/reviews/<slug>/views/` |

So a template is written once and reused by every review; each review's rendered files sit next to
the data they project, and are regenerated (never hand-edited) with:

```bash
python tools/build_views.py  <slug>     # → data/reviews/<slug>/views/<slug>-prisma.md, -extraction.md
python tools/build_report.py <slug>     # → data/reviews/<slug>/views/<slug>-report.html
```

`report.template.html` is a full self-contained page body (inline CSS + JS) with three placeholders
the tool substitutes: `__DATA__` (the review's protocol + records as JSON), `__SLUG__`, `__DATE__`.
Edit the template to change how *every* review renders; edit nothing here to change *one* review —
change its data and regenerate.

# Task: Implement Detailed Violation Reports Feature

## Goal
As a traffic enforcement officer, I want to generate detailed violation reports so that I can analyze traffic patterns and export evidence for legal proceedings.

## Context
- **Current Behavior:** Dashboard shows basic info, no export, limited analytics.
- **Missing:** PDF/CSV export, detailed filtering, specific report views.

## Action Items
1.  **Dependencies**:
    -   Add `reportlab` (for PDF) and `matplotlib` or similar (if backend charting needed) to `requirements.txt`.
2.  **Backend Implementation**:
    -   Create `app/routes/reports.py`.
    -   Implement `GET /reports` (Dashboard).
    -   Implement `GET /reports/generate` (Form).
    -   Implement `POST /reports/export` (PDF/CSV logic).
3.  **Frontend Implementation**:
    -   Create `app/templates/reports.html`.
    -   Create `app/templates/report_generate.html`.
    -   Add Charts (using Chart.js via CDN or local) for analytics.
4.  **Integration**:
    -   Register blueprint in `app/__init__.py`.
    -   Add navigation link in `base.html`.

## Acceptance Criteria
- [ ] User can generate reports with date range.
- [ ] Reports can be exported to PDF (with evidence images) and CSV.
- [ ] Charts display violation trends (e.g., violations over time).
- [ ] All filters (Date, Type, Location) work correctly.

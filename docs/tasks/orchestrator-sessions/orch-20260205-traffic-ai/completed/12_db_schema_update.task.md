# Task: Update Database Schema with Extended Entity Model

## Goal
The current database schema needs to be extended to support vehicle owners, traffic officers, and camera management. This will enable better tracking of violations and responsible parties. Additionally, the existing `Violation` table is out of sync with its model and needs updating.

## Context
**Current State:**
- `app/models.py` contains `Violation` with video playback fields (`frame_number`, `video_fps`, `video_path`), but these are **missing** in the actual database (according to `89e5ebe0580e_fresh_init.py`).
- Missing `Owner`, `Vehicle`, `TrafficOfficer`, and `Camera` entities from `GITHUB_ISSUES.md`.

**Proposed Schema:**
1.  **Owner:** `id`, `owner_name`, `address`, `phone_number`, `email`, `created_at`.
2.  **Vehicle:** `id`, `license_plate` (renamed from `plate_number` for consistency), `vehicle_type`, `owner_id` (FK), `created_at`.
3.  **TrafficOfficer:** `id`, `officer_name`, `badge_number`, `email`, `role`, `created_at`.
4.  **Camera:** `id`, `location`, `status`, `stream_url`, `created_at`.
5.  **Violation (Update):** 
    -   Add `frame_number`, `video_fps`, `video_path` (sync fix).
    -   Add FKs to `Vehicle`, `Camera`, `TrafficOfficer`.

## Action Items
1.  **Sync and Extend `app/models.py`**:
    -   Ensure all current `Violation` fields are in the model.
    -   Define `Owner`, `Vehicle`, `TrafficOfficer`, `Camera` classes.
    -   Update `Violation` class with foreign keys and relationships.
2.  **Execute Migrations**:
    -   Run `flask db migrate -m "extend_schema_and_sync_violation"`
    -   Run `flask db upgrade`
3.  **Data Migration (Optional/Refinement)**:
    -   Script to move existing `license_plate` data from `violations` to `vehicles` table if necessary.
4.  **Update Routes and Admin UI**:
    -   Update `app/routes/admin.py` to handle the new tables.
    -   Update `app/templates/admin.html` to reflect the extended schema.

## Acceptance Criteria
- [ ] `Violation` table columns match `app/models.py` (including video fields).
- [ ] `Owner`, `Vehicle`, `TrafficOfficer`, `Camera` models exist and are linked.
- [ ] Database migration script is applied successfully.
- [ ] Admin interface allows viewing and adding records to all 5 tables.
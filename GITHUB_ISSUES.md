# GitHub Issues - Ready to Copy

## Issue 1: Add Detailed Violation Reports Feature

---

**Title:** Implement Detailed Violation Reports Feature

**Labels:** `enhancement`, `feature`

**Description:**

As a traffic enforcement officer, I want to generate detailed violation reports so that I can analyze traffic patterns and export evidence for legal proceedings.

**Current Behavior:**
- The dashboard shows basic violation information
- No export functionality for reports
- Limited analytics and filtering options

**Proposed Behavior:**

Add a new "Reports" section with the following features:

### Core Features
1. **Report Types:**
   - Daily Violation Summary
   - Weekly/Monthly Analytics
   - Vehicle-wise Report
   - Location-based Report
   - Officer Activity Report

2. **Export Options:**
   - PDF Export with evidence images
   - CSV Export for data analysis
   - Print-friendly format

3. **Filtering:**
   - Date range picker
   - Violation type filter
   - Location/Camera filter
   - Status filter (paid/pending)

4. **Analytics:**
   - Charts showing violation trends
   - Top violating vehicles
   - Hotspot locations
   - Officer performance metrics

### Technical Implementation

**New Routes:**
- `GET /reports` - Reports dashboard
- `GET /reports/generate` - Generate report form
- `POST /reports/export` - Export report

**New Templates:**
- `app/templates/reports.html`
- `app/templates/report_generate.html`

**Dependencies:**
- ReportLab or similar for PDF generation
- Chart.js for visualizations

**Acceptance Criteria:**
- [ ] User can generate reports with date range
- [ ] Reports can be exported to PDF and CSV
- [ ] Evidence images are included in PDF reports
- [ ] Charts display violation trends
- [ ] All filters work correctly

---

## Issue 2: Update Database Schema with Extended Entity Model

---

**Title:** Update Database Schema - Add Owner, TrafficOfficer, and Camera Entities

**Labels:** `enhancement`, `database`, `refactor`

**Description:**

The current database schema needs to be extended to support vehicle owners, traffic officers, and camera management. This will enable better tracking of violations and responsible parties.

**Current Schema (Partial):**
- Violation entity exists
- Limited entity relationships

**Proposed Schema:**

### Entity: Owner
Represents vehicle owners in the system.

| Attribute | Type | Description |
|-----------|------|-------------|
| id | Integer, PK | Unique owner identifier |
| owner_name | String | Full name of owner |
| address | Text | Owner address |
| phone_number | String | Contact number |
| email | String | Email address |
| created_at | DateTime | Record creation timestamp |

### Entity: Vehicle
Represents individual vehicles registered in the system.

| Attribute | Type | Description |
|-----------|------|-------------|
| id | Integer, PK | Unique vehicle identifier |
| plate_number | String | License plate number |
| vehicle_type | String | Car, truck, motorcycle, etc. |
| owner_id | Integer, FK | Reference to Owner |
| created_at | DateTime | Record creation timestamp |

### Entity: Violation
The central entity for traffic incidents.

| Attribute | Type | Description |
|-----------|------|-------------|
| id | Integer, PK | Unique violation identifier |
| vehicle_id | Integer, FK | Reference to Vehicle |
| camera_id | Integer, FK | Reference to Camera |
| officer_id | Integer, FK | Reference to TrafficOfficer |
| date_time | DateTime | When violation occurred |
| violation_type | String | Type of violation |
| penalty | Float | Penalty amount |
| status | String | pending/paid/disputed |
| evidence_image | String | Path to evidence image |
| description | Text | Additional details |

### Entity: TrafficOfficer
Represents personnel who issue or review violations.

| Attribute | Type | Description |
|-----------|------|-------------|
| id | Integer, PK | Unique officer identifier |
| officer_name | String | Full name |
| badge_number | String | Badge number |
| email | String | Official email |
| role | String | admin/editor/viewer |
| created_at | DateTime | Record creation timestamp |

### Entity: Camera
Represents automated detection cameras.

| Attribute | Type | Description |
|-----------|------|-------------|
| id | Integer, PK | Unique camera identifier |
| location | String | Physical location |
| status | String | active/inactive/maintenance |
| stream_url | String | Video stream URL |
| created_at | DateTime | Record creation timestamp |

### Relationships:
- One Owner has Many Vehicles
- One Vehicle has Many Violations
- One Camera has Many Violations
- One TrafficOfficer has Many Violations

### Migration Steps:

1. **Create new tables:**
   ```bash
   flask db revision "create_owner_table"
   flask db revision "create_vehicle_table"
   flask db revision "create_officer_table"
   flask db revision "create_camera_table"
   ```

2. **Update existing violation table:**
   ```bash
   flask db revision "add_foreign_keys_to_violation"
   ```

3. **Data migration:**
   - Extract plate numbers to vehicle table
   - Create owner records
   - Link existing violations to new entities

### Files to Modify:
- `app/models.py` - Add new model classes
- `app/routes/violations.py` - Update CRUD operations
- `app/routes/admin.py` - Add officer/camera management
- `app/templates/admin.html` - Add management UI

### Acceptance Criteria:
- [ ] Owner model created with all attributes
- [ ] Vehicle model created with owner FK
- [ ] TrafficOfficer model created
- [ ] Camera model created
- [ ] Violation table updated with FKs
- [ ] Relationships properly defined in SQLAlchemy
- [ ] Admin interface allows managing all entities
- [ ] Existing data is preserved/migrated

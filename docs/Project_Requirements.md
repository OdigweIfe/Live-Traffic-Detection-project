# TrafficAI - Project Requirements Document (PRD)

## Project Overview

**Project Name:** TrafficAI  
**Version:** 1.0 (MUS - Minimum Usable State)  
**Mission:** To develop an automated traffic violation detection system that uses CCTV footage and Computer Vision to improve road safety, reduce manual surveillance burden, and enable consistent enforcement of traffic laws.

**Tech Stack:**
- **Backend:** Python + Flask
- **AI/ML:** YOLOv8 + OpenCV + PyTorch
- **Frontend:** HTML + CSS + JavaScript + Bootstrap (or Next.js + Tailwind CSS for modern alternative)
- **Database:** SQLite (lightweight, file-based)
- **Training Environment:** Google Colab (for GPU-accelerated model training)

---

## Functional Requirements

| Requirement ID | Description | User Story | Expected Behavior / Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| FR-001 | Video Upload & Processing | As a traffic officer, I want to upload CCTV footage, so that the system can analyze it for violations. | User can upload video files (.mp4, .avi) via web interface. System processes the video frame-by-frame. | MUS |
| FR-002 | Vehicle Detection (YOLO) | As a system, I need to detect vehicles in video frames, so that I can track their movement. | YOLOv8 model detects and classifies vehicles (car, truck, motorcycle, bus) with bounding boxes. | MUS |
| FR-003 | Red Light Violation Detection | As a traffic officer, I want the system to detect red-light running, so that violators can be identified. | System defines a virtual stop line. If a vehicle crosses the line while the traffic signal is red, a violation is logged. | MUS |
| FR-004 | Speed Estimation & Violation Detection | As a traffic officer, I want the system to estimate vehicle speed and flag overspeeding, so that speed violations are captured. | System calculates vehicle speed based on frame-to-frame displacement. If speed exceeds a pre-defined threshold, a violation is logged. | MUS |
| FR-005 | Lane Violation Detection | As a traffic officer, I want to detect illegal lane changes, so that unsafe driving is identified. | System defines lane boundaries. If a vehicle crosses without indication or improperly, a violation is logged. | MUS |
| FR-006 | Basic License Plate Recognition (ANPR) | As a traffic officer, I want the system to extract license plate numbers, so that violations can be linked to specific vehicles. | System crops vehicle region and uses OCR (Tesseract/EasyOCR) to extract plate text. Plate number is stored with the violation. | MUS |
| FR-007 | Violation Logging to Database | As a system, I need to store all detected violations, so that they can be reviewed later. | Each violation is saved to MySQL database with: timestamp, violation type, vehicle type, license plate, frame image, location (if available). | MUS |
| FR-008 | Dashboard - View Violations | As a traffic officer, I want to view all detected violations on a dashboard, so that I can review and take action. | Web dashboard displays a table of violations with sortable columns: timestamp, type, vehicle, plate, and a thumbnail image. | MUS |
| FR-009 | Dashboard - Filter & Search | As a traffic officer, I want to filter violations by type and date, so that I can focus on specific incidents. | Dashboard has dropdown filters for violation type (red light, speed, lane) and date range picker. Search bar for license plate lookup. | MUS |
| FR-010 | Dashboard - View Violation Details | As a traffic officer, I want to click on a violation to see full details, so that I can verify the incident. | Clicking a violation row opens a modal/detail page showing: full image, video clip (if available), metadata (time, speed, location). | MUS |
| FR-011 | Traffic Signal State Detection | As a system, I need to detect traffic light color (red, yellow, green), so that red-light violations can be validated. | Computer vision algorithm (color detection or pre-defined ROI) identifies signal state in each frame. | MUS |
| FR-012 | Region of Interest (ROI) Configuration | As a system administrator, I want to define ROI zones (stop line, lanes, speed zones), so that detection is accurate. | Admin interface or config file allows defining polygon ROIs for stop lines, lanes, and speed measurement zones. | MUS |
| FR-013 | Video Batch Processing | As a traffic officer, I want to upload multiple videos at once, so that I can process batches of footage efficiently. | System accepts multiple file uploads. Processes them sequentially or in parallel (queue-based). | Future |
| FR-014 | Real-Time CCTV Stream Processing | As a traffic officer, I want to connect live CCTV streams, so that violations are detected in real-time. | System accepts RTSP/HTTP stream URLs. Processes live video and logs violations as they occur. | Future |
| FR-015 | Advanced Analytics Dashboard | As a traffic administrator, I want to see violation trends over time, so that I can identify high-risk areas. | Dashboard includes charts (bar, line, heatmap) showing violations by type, location, time of day, and day of week. | Future |
| FR-016 | Automated Report Generation | As a traffic administrator, I want to generate PDF reports of violations, so that I can share them with authorities. | System generates downloadable PDF reports with violation summaries, images, and statistics. | Future |
| FR-017 | User Authentication & Roles | As a system administrator, I want role-based access control, so that only authorized users can view/manage violations. | Login system with roles: Admin (full access), Officer (view/search), Guest (read-only). | Future |
| FR-018 | Notification System | As a traffic officer, I want to receive alerts when critical violations occur, so that I can respond immediately. | System sends email/SMS/push notifications for high-priority violations (e.g., excessive speeding). | Future |
| FR-019 | Vehicle Tracking Across Frames | As a system, I need to track individual vehicles across multiple frames, so that I can analyze their trajectory. | Implements object tracking (DeepSORT or ByteTrack) to assign unique IDs to vehicles and follow them through the video. | Future |
| FR-020 | Fine Calculation & Integration | As a traffic administrator, I want the system to calculate fines based on violation type, so that enforcement is standardized. | System references a fine table and calculates penalties. Integration with payment/ticketing systems (out of scope for MUS). | Future |

---

## Non-Functional Requirements

| Requirement ID | Description | Acceptance Criteria |
| :--- | :--- | :--- |
| NFR-001 | Performance | System processes video at ≥15 FPS on standard hardware (CPU). Real-time processing achieved with GPU. |
| NFR-002 | Accuracy | Vehicle detection accuracy ≥85%. Violation detection accuracy ≥80%. ANPR accuracy ≥70% under good conditions. |
| NFR-003 | Scalability | System architecture supports adding new violation types and detection algorithms without major refactoring. |
| NFR-004 | Usability | Dashboard is intuitive and requires <5 minutes of training for new users. |
| NFR-005 | Maintainability | Code follows PEP 8 (Python). Modular design allows easy updates to AI models or database schema. |
| NFR-006 | Compatibility | Works on Windows (primary), Linux (secondary). Compatible with common CCTV formats (MP4, AVI, MKV). |
| NFR-007 | Data Security | Violation data stored securely. Database access requires authentication. No public exposure of sensitive data. |

---

## System Constraints

- **No Physical Hardware Setup:** This is a software prototype. Assumes CCTV footage is already available.
- **No GPU on Local Machine:** Training and heavy inference will use Google Colab.
- **Limited to Pre-Recorded Video for MUS:** Real-time CCTV streaming is a future feature.
- **Academic Scope:** Not intended for production deployment with legal enforcement integration in MUS.
- **Lightweight Database:** SQLite is used for simplicity; production deployment may require PostgreSQL or MySQL.

---

## Success Criteria (MUS)

1. ✅ System successfully detects vehicles in uploaded video.
2. ✅ Red-light violations are accurately identified and logged.
3. ✅ Speed violations are detected with reasonable accuracy (±10% margin).
4. ✅ Lane violations are flagged based on defined ROI.
5. ✅ License plates are extracted and stored (even if OCR accuracy is moderate).
6. ✅ Dashboard displays all violations in a clean, filterable table.
7. ✅ Violation details (image, metadata) are viewable on click.

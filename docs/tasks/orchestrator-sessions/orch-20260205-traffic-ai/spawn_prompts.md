# Sub-Agent Spawn Prompts

**Session ID:** orch-20260205-traffic-ai
**Created:** 2026-02-05 22:56

---

## Execution Order

```
Task 01 (Sequential) ─► Task 02 + 04 (Parallel) ─► Task 03 (Sequential) ─► Task 05 (Sequential)
     │                      │             │
     │                      │             │
  [Verify Setup]      [Run Tests]    [UI Polish]
                           │
                           ▼
                    [Improve Coverage]
                           │
                           ▼
                    [Create Walkthrough]
```

**Why this order:**
- 01 must run first (environment verification)
- 02 & 04 are read-only, can safely run in parallel
- 03 writes to `tests/`, must wait for 02 results
- 05 needs all results for final walkthrough

---

## How to Run

Copy each command below into PowerShell in the project directory:

```powershell
cd "c:\CreativeOS\01_Projects\Clients\Final Yeah Projects 2026\2026-02-05_Live-Traffic-Detection-project"
```

---

## Task 01: Verify Setup (Run First)

```powershell
gemini -m gemini-3-pro-preview --approval-mode yolo "You are executing task 01_verify_setup.task.md from orchestrator session orch-20260205-traffic-ai.

## Objective
Verify the TrafficAI project environment is correctly set up.

## Steps
1. Check Python version (must be 3.10+)
2. Verify virtual environment exists, create if needed
3. Install requirements: pip install -r requirements.txt
4. Apply database migrations: flask db upgrade
5. Test Flask app starts: flask run (then Ctrl+C after confirming)
6. Verify dashboard loads by checking the route exists

## Output Required
Create file: docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/01_verify_setup.result.md

Include:
- Python version found
- Packages installed (success/failure)
- Database migration status
- Flask startup status
- Any errors encountered

DO NOT fix issues, just document them."
```

---

## Task 02: Run Tests (After Task 01)

```powershell
gemini -m gemini-3-pro-preview --approval-mode yolo "You are executing task 02_run_tests.task.md from orchestrator session orch-20260205-traffic-ai.

## Objective
Run the complete pytest suite and document results.

## Steps
1. Activate virtual environment: .\venv\Scripts\activate
2. Run tests: pytest -v
3. Run with coverage: pytest --cov=app --cov-report=term-missing
4. Document all passing and failing tests

## Output Required
Create file: docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/02_run_tests.result.md

Include:
- Total tests run
- Pass/fail counts
- Coverage percentage
- List of failing tests with error summaries
- Root cause analysis for major failures

Fix simple issues if obvious (missing imports, typos). Document significant problems."
```

---

## Task 04: UI Polish (Can Run Parallel with Task 02)

```powershell
gemini -m gemini-3-pro-preview --approval-mode yolo "You are executing task 04_ui_polish.task.md from orchestrator session orch-20260205-traffic-ai.

## Objective
Verify all frontend templates work correctly.

## Steps
1. Start Flask app: flask run
2. Verify each template renders:
   - GET / (index/upload page)
   - GET /dashboard
   - GET /admin
   - GET /summary
3. Check for JavaScript console errors
4. Test dashboard filtering UI elements exist
5. Document any CSS/JS issues

## Output Required
Create file: docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/04_ui_polish.result.md

Include:
- Each page tested and status
- Any rendering errors
- Missing UI elements
- Suggested improvements

This is a verification task - minimal code changes unless critical."
```

---

## Task 03: Improve Coverage (After Task 02)

```powershell
gemini -m gemini-3-pro-preview --approval-mode yolo "You are executing task 03_improve_coverage.task.md from orchestrator session orch-20260205-traffic-ai.

## Objective
Improve test coverage to ≥70% by adding missing tests.

## Context
From GitHub Issues, these tests are incomplete:
- Issue #7: Speed estimation accuracy within ±10% margin
- Issue #9: ANPR OCR accuracy test, unit test with sample images
- Issue #15: Test coverage ≥70%

## Steps
1. Review current test files in tests/
2. Add missing ANPR unit tests to tests/test_anpr.py
3. Add speed accuracy validation test to tests/test_violations.py or new file
4. Run pytest --cov=app to verify coverage improvement
5. Fix any new test failures

## Output Required
Create file: docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/03_improve_coverage.result.md

Include:
- Tests added (file, function names)
- New coverage percentage
- Any issues encountered"
```

---

## Task 05: Create Walkthrough (Run Last)

```powershell
gemini -m gemini-3-pro-preview --approval-mode yolo "You are executing task 05_walkthrough.task.md from orchestrator session orch-20260205-traffic-ai.

## Objective
Create final project walkthrough documenting completed work.

## Context
Read the result files from:
- docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/01_verify_setup.result.md
- docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/02_run_tests.result.md
- docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/03_improve_coverage.result.md
- docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/completed/04_ui_polish.result.md

## Steps
1. Read all result files
2. Summarize project status
3. Document what's complete vs remaining
4. Create handoff-ready walkthrough

## Output Required
Create file: docs/tasks/orchestrator-sessions/orch-20260205-traffic-ai/walkthrough.md

Include:
- Project overview
- Features completed (MUS checklist)
- Test results summary
- UI verification results
- Known issues
- Deployment recommendations
- Next steps"
```

---

## Quick Reference

| Task | Depends On | Writes To | Safe Parallel? |
|------|------------|-----------|----------------|
| 01   | None       | result file only | N/A (first) |
| 02   | 01         | result file only | ✅ Yes with 04 |
| 04   | 01         | result file only | ✅ Yes with 02 |
| 03   | 02         | tests/ directory | ❌ Sequential |
| 05   | All        | walkthrough.md   | N/A (last) |

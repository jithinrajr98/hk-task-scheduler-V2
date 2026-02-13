# Product Requirement Document: HK Task Scheduler V2

**Created**: 2026-02-13
**Version**: 1.0
**Status**: Draft
**Complexity**: Medium

---

## Executive Summary

A Streamlit web application that generates daily housekeeping schedules for a luxury furniture gallery. Users upload staff schedules (Excel/CSV), select a day, and the app uses Groq LLM to produce a constraint-respecting task assignment displayed as a horizontal timeline grid.

## Problem & Users

**Problem**: Manual creation of daily housekeeping schedules for a multi-floor luxury gallery is time-consuming and error-prone, with complex constraints around staffing, task timing, and no-double-booking rules.

**Users**: Gallery housekeeping managers who need to produce a valid daily schedule given varying staff availability (11-20 people, different days off).

## Goals & Success Criteria

### Product Goals
1. Automate daily schedule generation with zero constraint violations
2. Provide a clear visual timeline so managers can see at a glance who does what and when
3. Minimize time from "upload schedule" to "ready-to-print schedule" (< 30 seconds)

### Acceptance Criteria
- [ ] User can upload Excel or CSV staff schedule file
- [ ] User can select a day of the week to generate a schedule for
- [ ] App filters staff available for shift_1 (07:00-15:00) on the selected day
- [ ] App sends structured prompt to Groq LLM and receives valid JSON schedule
- [ ] Schedule displayed as horizontal timeline grid (employees as rows, hours 07-14 as columns)
- [ ] Task blocks are color-coded by task category
- [ ] No constraint violations in generated schedule
- [ ] Error handling for API failures, invalid uploads, and insufficient staff

## Core Features

### Must Have (P0 - MVP)

1. **File Upload** — Accept Excel (.xlsx) and CSV (.csv) staff schedule files, parse into structured format (name, day, shift_name, start_time, end_time), validate on upload. Effort: Low

2. **Day Selection** — Dropdown for day of the week (Monday-Sunday), filter staff to shift_1 (07:00-15:00), display available staff count. Effort: Low

3. **LLM Schedule Generation** — Use exact prompt structure from `hk_prompt.ipynb` (TASK_CONTEXT, TASK_DESCRIPTION, EXAMPLES, INPUT_DATA, CONSTRAINT, PRECOGNITION, OUTPUT_FORMATTING). Reuse/improve the `get_completion()` function from the notebook. Call Groq API with `meta-llama/llama-4-scout-17b-16e-instruct`. Parse JSON response. API key from `GROQ_API_KEY` env variable. Effort: Medium

4. **Timeline Grid Display** — Horizontal Gantt-chart style grid. Rows: one per employee (name + shift time). Columns: hourly slots 07:00-14:00. Color-coded task blocks by category (floors, restrooms, outdoor, egress, BOH, float, break). Minimalistic — no images/avatars. Effort: High

5. **Constraint Validation Display** — Post-generation validation showing pass/fail per constraint. Effort: Medium

### Should Have (P1)

6. **Regenerate Button** — Re-run generation if result is unsatisfactory. Effort: Low

7. **Schedule Export** — Download as CSV or printable format. Effort: Low

### Nice to Have (P2)

8. **Manual Override** — Click-to-edit individual task assignments. Effort: High

## Technical Approach

### Architecture
- **Frontend**: Streamlit single-page app
- **LLM**: Groq API via `groq` Python SDK — reuse `get_completion()` from notebook with improvements (env var for API key, error handling, JSON extraction)
- **Data**: Pandas for Excel/CSV parsing
- **Display**: Custom HTML/CSS rendered via `st.html()` for the timeline grid

### `get_completion()` Integration
The notebook's function will be adapted:
```python
# From hk_prompt.ipynb - to be reused/improved
def get_completion(prompt, system_prompt="", prefill=""):
    # Uses Groq SDK, model: meta-llama/llama-4-scout-17b-16e-instruct
    # temperature=0.0, max_tokens=2000
    # Returns prefill + response content
```
Improvements: read API key from env, add retry logic, extract JSON from `<response>` tags.

### Prompt Assembly
Exact prompt variables from notebook: TASK_CONTEXT, TASK_DESCRIPTION, EXAMPLES (with expected_output), INPUT_DATA (day_schedule), CONSTRAINT, PRECOGNITION, OUTPUT_FORMATTING, PREFILL.

### Data Flow
1. Excel/CSV upload → Pandas → staff_schedule list
2. Day selection → filter shift_1 → day_schedule
3. day_schedule → prompt template → `get_completion()` → JSON response
4. Parse assignments → render timeline grid

## Task Schedule Reference

### Opening Duties (07:00-10:00)
| Time | Task | Staffing |
|------|------|----------|
| 07:00-08:00 | Floor_-1 | 1 person (moves to Floor_3 at 08:00) |
| 07:00-09:00 | Floor_0 | 1-2 people |
| 07:00-09:00 | Floor_1 | 1-2 people |
| 07:00-09:00 | Floor_2 | 2 people mandatory |
| 07:00-09:00 | Floor_4 | 1-2 people |
| 09:00-10:00 | Outdoor areas | All staff, min 1 per area |

### Regular Tasks (10:00-15:00)
| Task | Time | Staffing |
|------|------|----------|
| Egress | 10:00-12:00 | Exactly 2 |
| BOH-Breakroom | 10:00-11:00 & 14:00-15:00 | Exactly 1 |
| BOH-Restrooms | 10:00-11:00 & 14:00-15:00 | Exactly 1 |
| Restroom_2 | 10:00-15:00 | 1-2 (2 from 14:00), max 2h/person |
| Restroom_4 | 10:00-15:00 | Exactly 1, max 2h/person |
| Float_ALL/0/1/-1 | 1h between 11:00-15:00 | 1 person each |

## Constraints (Strictly Enforced)

- No double-booking staff across simultaneous tasks
- Restroom_2: min 1, max 2 at all times; 2 mandatory from 14:00; max 2h/person
- Restroom_4: exactly 1 at all times; max 2h/person
- Egress: exactly 2 people, 10:00-12:00 only
- BOH-Breakroom: exactly 1 person, only at 10:00-11:00 and 14:00-15:00
- BOH-Restrooms: exactly 1 person, only at 10:00-11:00 and 14:00-15:00
- Each staff gets 1-hour break between 11:00-13:00

## Out of Scope (V1)

- Shift_2 and Shift_3 scheduling
- Multi-day generation
- Staff roster management
- Drag-and-drop editing
- User authentication / database persistence

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM generates constraint-violating schedule | High | Post-generation validation + regenerate |
| LLM returns malformed JSON | Medium | Regex fallback parsing + error message |
| Groq API downtime | Medium | Clear error messaging, retry button |
| Insufficient staff (< 6) | Medium | Pre-check count, warn user |

## Next Steps

**Greenfield project** — enter EPCC workflow:
1. Review & approve this PRD
2. `/epcc-plan` to create implementation plan
3. `/epcc-code` to build
4. `/epcc-commit` to finalize

---

**End of PRD**

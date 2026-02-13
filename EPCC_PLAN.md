# Plan: HK Task Scheduler V2

**Created**: 2026-02-13 | **Effort**: ~6h | **Complexity**: Medium

## 1. Objective

**Goal**: Streamlit app that generates daily housekeeping schedules using Groq LLM and displays them as a color-coded timeline grid.

**Why**: Automate manual schedule creation for a luxury gallery's housekeeping team.

**Success**: Upload works, schedule generates in <30s, timeline grid renders correctly, constraints validated.

## 2. Approach

- **Single-file Streamlit app** (`app.py`) with helper modules kept minimal
- **Prompt logic**: Lift directly from `hk_prompt.ipynb` — reuse `get_completion()`, all prompt variables, and example output as-is
- **Data**: Ship `data/staff_schedule.json` as bundled default; also support Excel/CSV upload via `st.file_uploader`
- **Timeline Grid**: Custom HTML/CSS rendered via `st.html()` — use `frontend-design` skill for a polished, minimalistic Gantt chart
- **Validation**: Simple Python functions checking constraints post-generation
- **UI Validation**: Playwright MCP to verify the app renders correctly in browser
- **API Key**: `GROQ_API_KEY` environment variable (never hardcoded)

**Trade-off**: Single `app.py` + one `prompt.py` module vs multi-file structure → chose minimal files for simplicity, matching user preference.

## 3. Tasks

### Phase 1: Core Backend (~2h)

1. **Create `prompt.py`** (1h) — Extract `get_completion()` and all prompt variables (TASK_CONTEXT, TASK_DESCRIPTION, EXAMPLES, INPUT_DATA, CONSTRAINT, PRECOGNITION, OUTPUT_FORMATTING) from notebook. Add JSON parsing from `<response>` tags. Use env var for API key.
   - Deps: None | Risk: Low

2. **Create `app.py` with upload + day selection** (1h) — File uploader (xlsx/csv), day dropdown, staff filtering to shift_1, display available count. Parse uploaded file with pandas or fall back to bundled `data/staff_schedule.json`.
   - Deps: Task 1 | Risk: Low

### Phase 2: Generation + Display (~2.5h)

3. **Add schedule generation flow** (0.5h) — "Generate" button wires day_schedule into prompt template, calls `get_completion()`, parses JSON response. Add regenerate button.
   - Deps: Task 2 | Risk: Medium (LLM may return malformed JSON)

4. **Build timeline grid UI** (1.5h) — Use `frontend-design` skill. Horizontal Gantt: employee rows, hourly columns (07-14), color-coded blocks by category. Render via `st.html()`. Minimalistic design.
   - Deps: Task 3 | Risk: Low

5. **Add constraint validation display** (0.5h) — Check no double-booking, restroom staffing, egress count, BOH rules. Show pass/fail indicators below the grid.
   - Deps: Task 3 | Risk: Low

### Phase 3: Polish + Test (~1.5h)

6. **Add CSV export** (0.5h) — Download button for generated schedule as CSV.
   - Deps: Task 5 | Risk: Low

7. **Write bare minimum tests** (0.5h) — Test staff filtering, JSON parsing, constraint validation functions. No UI tests in pytest — use Playwright MCP instead.
   - Deps: Task 5 | Risk: Low

8. **Playwright MCP UI validation** (0.5h) — Launch app, verify page loads, upload works, grid renders, colors appear. Manual validation via Playwright browser tools.
   - Deps: Task 6, 7 | Risk: Low

**Total**: ~6h

## 4. Quality Strategy

**Tests**: Bare minimum pytest — staff filtering logic, JSON response parsing, constraint validation functions (~3-5 tests).

**UI Validation**: Playwright MCP to visually verify timeline grid renders, color coding works, and upload flow functions.

## 5. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM returns malformed JSON | Medium | Regex fallback to extract JSON from response tags |
| Groq API rate limit / downtime | Medium | Clear error message + regenerate button |
| Insufficient staff for valid schedule | Low | Pre-check count, warn if < 6 |

**Assumptions**: Groq API available, `meta-llama/llama-4-scout-17b-16e-instruct` model accessible, user has `GROQ_API_KEY` set.

**Out of scope**: Shift_2/3, multi-day, drag-and-drop editing, auth, database.

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

**Out of scope**: Multi-day, drag-and-drop editing, auth.

---

# Plan: Add Shift 2 & Shift 3 Support

**Created**: 2026-02-17 | **Effort**: ~2h | **Complexity**: Medium

## 1. Objective

**Goal**: Extend schedule generation from shift_1-only to all 3 shifts in a single combined LLM call and display a full-day 07:00-22:00 timeline.

**Why**: The gallery operates across 3 shifts (07:00-15:00, 13:00-21:00, 15:00-23:00). Shift_1-only scheduling left afternoon/evening uncovered.

**Success**:
- All shifts' staff sent to LLM in one call
- Timeline grid spans 07:00-22:00 (16 columns)
- Constraint validation covers full operating hours
- All 10 tests pass

## 2. Approach

- **Single LLM call**: Send all shifts' staff for the selected day (not just shift_1). The prompt's `EXPECTED_OUTPUT` already updated with shift_2/shift_3 examples.
- **Extended timeline**: Expand `TIME_SLOTS` from 8 slots (07:00-14:00) to 16 slots (07:00-22:00). Empty cells for hours outside a staff member's shift show the existing hatched pattern.
- **Dynamic constraint ranges**: Restroom_2 and Restroom_4 validation extended to cover 10:00-22:00 based on actual time slots present in assignments.
- **Backward compatible**: Egress and BOH constraints keep their original time ranges (shift_1-specific tasks).

**Trade-off**: Dynamic time ranges from `time_map` keys vs hardcoded extended ranges → chose dynamic for robustness (adapts to whatever the LLM outputs).

## 3. Tasks

### Phase 1: Fix prompt.py bugs (~0.5h)

1. **Fix missing comma in EXPECTED_OUTPUT** (5min) — Line 77: `"13:00": "Outside"` missing trailing comma | Deps: None | Risk: Low
2. **Fix double-encoding of EXPECTED_OUTPUT** (10min) — `json.dumps()` on a string double-encodes. Use string directly in `build_prompt()` | Deps: None | Risk: Low
3. **Increase max_tokens** (5min) — 2000→4000 for multi-shift responses | Deps: None | Risk: Low

### Phase 2: Update app.py (~1h)

4. **Replace filter_shift1 with filter_by_day** (10min) — Remove shift_name filter, return all staff for selected day | Deps: None | Risk: Low
5. **Expand TIME_SLOTS** (5min) — 07:00-14:00 → 07:00-22:00 (16 columns) | Deps: None | Risk: Low
6. **Update sidebar UI labels** (5min) — "Available staff (Shift 1)" → "Available staff", "No shift_1 staff" → "No staff" | Deps: Task 4 | Risk: Low
7. **Extend constraint validation ranges** (30min) — Restroom_2/Restroom_4: dynamic 10:00-22:00 from time_map. Egress/BOH: unchanged. | Deps: None | Risk: Medium

### Phase 3: Update tests (~0.5h)

8. **Update test imports and filter tests** (15min) — Rename filter_shift1→filter_by_day, expect 3 results for Monday (all shifts) | Deps: Task 4 | Risk: Low
9. **Add multi-shift staff to VALID_ASSIGNMENTS** (15min) — Add shift_2/shift_3 employees G, H, I with evening time ranges | Deps: Task 7 | Risk: Low

**Total**: ~2h

## 4. Quality Strategy

**Tests**: Update existing 10 tests — no new test count, but expanded coverage for multi-shift data.
**Validation**: `uv run pytest -v` — all 10 pass. Manual verification via `uv run streamlit run app.py`.

## 5. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| max_tokens still insufficient for large teams | Medium | Increased to 4000; monitor and bump if needed |
| LLM struggles with 3-shift complexity | Medium | EXPECTED_OUTPUT provides clear multi-shift example |
| Timeline grid too wide at 16 columns | Low | Already has overflow-x: auto scrolling |

**Assumptions**: LLM can handle combined 8+ staff across 3 shifts within 4000 tokens.

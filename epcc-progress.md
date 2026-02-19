# EPCC Progress Log

**Project**: HK Task Scheduler V2
**Started**: 2026-02-13
**Progress**: 13/13 features (100%)

---

## Session 0: PRD Created - 2026-02-13

### Summary
Product Requirements Document created from initial idea exploration.

### Artifacts Created
- PRD.md - Product requirements
- epcc-features.json - Feature tracking (7 features)
- epcc-progress.md - This progress log

### Feature Summary
- **P0 (Must Have)**: 5 features (Upload, Day Select, LLM Generation, Timeline Grid, Validation)
- **P1 (Should Have)**: 2 features (Regenerate, Export)

### Key Decisions
- Streamlit + Python for frontend
- Groq LLM (meta-llama/llama-4-scout-17b-16e-instruct) for schedule generation
- Reuse `get_completion()` from hk_prompt.ipynb with improvements
- Timeline grid via custom HTML/CSS
- API key via GROQ_API_KEY environment variable

---

## Session 1: Planning Complete - 2026-02-13

### Summary
Implementation plan created. Minimal file structure: `prompt.py` + `app.py`. ~6h estimated effort.

---

## Session 2: Implementation Complete - 2026-02-13

### Summary
All 7 features implemented and verified via Playwright MCP E2E testing.

### Feature Progress
- F001: File Upload — verified
- F002: Day Selection — verified
- F003: LLM Schedule Generation — verified
- F004: Timeline Grid Display — verified (frontend-design skill)
- F005: Constraint Validation Display — verified
- F006: Regenerate Button — verified
- F007: Schedule Export — verified

### Files Created
- `prompt.py` — LLM prompt logic extracted from notebook
- `app.py` — Streamlit app with all features
- `tests/test_core.py` — 10 tests (all passing)
- `pyproject.toml` — uv project config
- `screenshots/` — Playwright validation screenshots

### Quality
- 10/10 tests passing
- Playwright MCP E2E validation complete
- Bug fixed: color mapping priority for BOH tasks

### Next Session
Run `/epcc-commit` to finalize.

---

## Session 3: Multi-Shift Support - 2026-02-17

### Summary
Extended schedule generation from shift_1-only to all 3 shifts (shift_1, shift_2, shift_3) in a single combined LLM call with full-day timeline.

### Changes Made
**prompt.py**:
- Fixed missing comma in EXPECTED_OUTPUT (line 77)
- Removed json.dumps() double-encoding of string EXPECTED_OUTPUT in build_prompt()
- Increased max_tokens from 2000 to 4000

**app.py**:
- Replaced `filter_shift1()` with `filter_by_day()` — returns all shifts for selected day
- Expanded TIME_SLOTS from 8 (07:00-14:00) to 16 (07:00-22:00)
- Updated sidebar labels: "Available staff (Shift 1)" → "Available staff"
- Extended Restroom_2/Restroom_4 constraint validation to dynamic 10:00-22:00 ranges

**tests/test_core.py**:
- Renamed filter_shift1 → filter_by_day in imports and tests
- test_filter_by_day_correct_day now expects 3 results (all shifts)
- Added shift_2/shift_3 employees (G, H, I) to VALID_ASSIGNMENTS fixture

### Feature Progress
- F008: Multi-Shift Staff Filtering — completed
- F009: Full-Day Timeline (07:00-22:00) — completed
- F010: Multi-Shift Constraint Validation — completed
- F011: Prompt Bug Fixes for Multi-Shift — completed

### Quality
- 10/10 tests passing (`uv run pytest -v`)

### Next Session
Run `/epcc-commit` to finalize multi-shift changes.

---

## Session 4: LLM Self-Correction - 2026-02-17

### Summary
Added automatic self-correction: when the first LLM pass fails constraint validation, a second pass with llama-3.3-70b-versatile fixes only the violated constraints.

### Changes Made
**prompt.py**:
- Added `CORRECTION_MODEL = "llama-3.3-70b-versatile"`
- Added `model` parameter to `get_completion()` (defaults to MODEL_NAME)
- Added `build_correction_prompt()` — builds targeted correction prompt with original schedule + failed rules + constraint rules
- Added `correct_schedule()` — orchestrates correction call using stronger 70b model

**app.py**:
- Imported `correct_schedule` from prompt
- After pass 1, runs `validate_constraints()` immediately
- If any constraint fails, calls `correct_schedule()` with "Correcting schedule..." spinner
- Max 1 correction attempt — no infinite loops

**tests/test_core.py**:
- Added `test_build_correction_prompt_includes_failures` — verifies failed rules appear, passing rules don't, original schedule JSON included

### Feature Progress
- F012: LLM Self-Correction via Second Pass — verified

### Quality
- 11/11 tests passing (`uv run pytest -v`)
- No regressions on existing features

### Next Session
Run `/epcc-commit` to finalize.

---

## Session 5: Switch LLM Provider to HuggingFace - 2026-02-17

### Summary
Switched LLM inference from Groq to HuggingFace router, simplified codebase by removing correction LLM second pass, and hardened response parsing for reasoning models.

### Changes Made
**prompt.py** (major refactor):
- Replaced `groq` SDK with `openai` SDK pointing at HuggingFace router (`https://router.huggingface.co/v1`)
- Model: `meta-llama/Llama-3.3-70B-Instruct` (user iterated through GLM-5, MiniMax-M2.5, gpt-oss-120b)
- Env var: `GROQ_API_KEY` → `HF_TOKEN`
- Removed `CORRECTION_MODEL`, `build_correction_prompt()`, `correct_schedule()` — single-pass generation only
- Removed `PREFILL` and prefill mechanism — eliminated double `<response>` tag bug
- Removed `PRECOGNITION` scratchpad instruction — prevented models wasting tokens on reasoning
- Condensed `TASK_DESCRIPTION` and `CONSTRAINT` prompts for clarity
- Added `<think>` and `<scratchpad>` stripping in `parse_response()` for reasoning model compatibility
- `temperature` → 0, `max_tokens` → 20000

**app.py**:
- Removed `correct_schedule` import and correction spinner block
- Generation flow simplified: generate → store (no second pass)

**pyproject.toml**:
- `groq>=1.0.0` → `openai>=1.0.0`

**tests/test_core.py**:
- Removed `build_correction_prompt` test (function deleted)
- Added `test_parse_response_with_think_tags` for reasoning model stripping

**CLAUDE.md**:
- Updated env vars, model references, architecture description

### Quality
- 11/11 tests passing (`uv run pytest -v`)

---

## Session 6: PNG Export with Playwright - 2026-02-19

### Summary
Replaced `html2image` PNG export with Playwright headless browser to fix timeline clipping issues. The `html2image` library used a fixed viewport that combined with CSS `max-width: 100%` to clip wide grids. Playwright's `full_page=True` screenshot captures the entire content.

### Changes Made
**app.py**:
- Replaced `html2image` import with `playwright.sync_api`
- PNG export writes timeline HTML to temp file, opens with headless Chromium, takes full_page screenshot
- Viewport width dynamically set to `len(TIME_SLOTS) * 120 + 300`
- HTML wrapper removes `max-width` constraint

**pyproject.toml**:
- Removed `html2image` dependency
- Added `playwright>=1.58.0`

### Feature Progress
- F013: PNG Export with Playwright — verified via Playwright MCP (full timeline captured, no clipping)

### Quality
- 11/11 tests passing (`uv run pytest -v`)
- Visual verification: PNG screenshot shows all 16 columns (07:00-22:00), all employee rows, legend

---

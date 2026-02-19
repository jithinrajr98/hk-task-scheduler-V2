# Implementation: HK Task Scheduler V2

**Mode**: default | **Date**: 2026-02-13 | **Status**: Complete

## 1. Changes (4 files created, 10 tests, all passing)

**Created**:
- `prompt.py` — `get_completion()`, prompt variables (TASK_CONTEXT, TASK_DESCRIPTION, EXAMPLES, CONSTRAINT, PRECOGNITION), `build_prompt()`, `parse_response()`, `generate_schedule()`
- `app.py` — Streamlit app: file upload, day selection, LLM generation, timeline grid (Swiss-utilitarian HTML/CSS), constraint validation, regenerate button, CSV export
- `tests/test_core.py` — 10 tests: staff filtering (2), JSON parsing (4), constraint validation (3), color mapping (1)

## 2. Quality

**Tests**: 10/10 passing (`uv run pytest`)
**UI Validation**: Playwright MCP — verified full E2E flow (upload, day select, generate, grid render, validation display, download button)
**Bug fixed**: `get_task_color()` matched "break" before "boh" for "BOH-Breakroom" — reordered checks

## 3. Decisions

**Single-file app**: All Streamlit logic in `app.py` for simplicity per user preference
**API key from env var**: `GROQ_API_KEY` — not hardcoded (notebook had it hardcoded)
**Bundled fallback data**: `data/staff_schedule.json` loaded when no file uploaded
**DM Sans font**: Google Font for timeline grid — falls back to system sans-serif

## 4. Handoff

**Run**: `HF_TOKEN=your_key uv run streamlit run app.py`
**Tests**: `uv run pytest`
**Ready for**: `/epcc-commit`
**Blockers**: None

---

# Implementation: LLM Provider Migration + PNG Export

**Mode**: default | **Date**: 2026-02-17 to 2026-02-19 | **Status**: Complete

## 1. Changes (4 files modified, +~120 lines, 11 tests)

**Modified**: `prompt.py` — Switched from Groq to HuggingFace router (OpenAI SDK), removed correction LLM, removed PREFILL/PRECOGNITION, added `<think>`/`<scratchpad>` stripping. Model: `meta-llama/Llama-3.3-70B-Instruct`.
**Modified**: `app.py` — Removed correction flow, added `random.shuffle()` for staff order, replaced `html2image` PNG export with Playwright headless browser for full-page screenshot.
**Modified**: `pyproject.toml` — `groq` → `openai`, `html2image` → `playwright`
**Modified**: `tests/test_core.py` — Removed correction test, added `test_parse_response_with_think_tags`

## 2. Quality

**Tests**: 11/11 passing. No regressions.
**PNG Export**: Verified via Playwright MCP — full timeline captured (07:00-22:00, all rows, legend) with no clipping.

## 3. Decisions

**HuggingFace over Groq**: User preference for HuggingFace inference router with broader model access.
**Single-pass generation**: Removed correction LLM second pass — simplifies codebase, single model only.
**Playwright over html2image**: `html2image` had viewport clipping issues with CSS `max-width: 100%`. Playwright's `full_page=True` screenshot captures complete content regardless of viewport.
**Staff randomization**: `random.shuffle()` before LLM call prevents positional bias in assignments.

## 4. Handoff

**Ready for**: `/epcc-commit`
**Blockers**: None

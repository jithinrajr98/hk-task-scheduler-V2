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

**Run**: `GROQ_API_KEY=your_key uv run streamlit run app.py`
**Tests**: `uv run pytest`
**Ready for**: `/epcc-commit`
**Blockers**: None

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py

# Run all tests (11 tests)
uv run pytest

# Run tests verbose
uv run pytest -v

# Run a single test
uv run pytest tests/test_core.py::test_filter_shift1_correct_day
```

## Environment Variables

Set in `.env` (loaded via python-dotenv):
- `HF_TOKEN` — required, for HuggingFace LLM inference
- `SUPABASE_URL` — optional, for persistent storage
- `SUPABASE_API_KEY` — optional, for persistent storage

For Streamlit Cloud deployment, these go in `.streamlit/secrets.toml` instead.

## Architecture

The app is a Streamlit single-page application that generates housekeeping task schedules for a luxury gallery using an LLM.

**Data flow:** Upload/load staff schedule → filter to shift_1 for selected day → send to HuggingFace LLM (Llama-3.3-70B) → display timeline grid → validate constraints → export CSV.

### Key Files

- `app.py` — Streamlit UI, file parsing, timeline HTML rendering, constraint validation
- `prompt.py` — LLM prompt assembly (structured sections: TASK_CONTEXT, TASK_DESCRIPTION, EXAMPLES, CONSTRAINT, etc.) and HuggingFace API calls via OpenAI SDK. Uses `meta-llama/Llama-3.3-70B-Instruct` at temperature 0.
- `supabase_client.py` — Supabase CRUD for `staff_schedule` table (push on upload, load on startup)
- `data/staff_schedule.json` — bundled fallback schedule data

### Data Loading Fallback Chain

1. User uploads Excel/CSV → parse + push to Supabase
2. No upload → load from Supabase
3. Supabase empty/unreachable → bundled JSON

### Schedule Data Shape

Each entry: `{ name, day, shift_name, start_time, end_time }`. Shift names: `shift_1` (07:00-15:00), `shift_2` (13:00-21:00), `shift_3` (15:00-23:00). Only shift_1 is used for task generation.

### LLM Response Format

The prompt instructs the LLM to wrap JSON in `<response>` tags. `parse_response()` strips reasoning blocks (`<think>`, `<scratchpad>`), extracts via regex, with a fallback that finds the first `{` to last `}`.

### Constraint Validation

`validate_constraints()` checks 6 rules against the generated schedule: no double-booking, Restroom_2/Restroom_4 staffing levels, Egress (exactly 2 at 10:00-11:00), BOH-Breakroom and BOH-Restrooms (exactly 1 at 10:00 and 14:00).

### Timeline Rendering

`build_timeline_html()` produces a self-contained HTML/CSS grid with color-coded task blocks (TASK_COLORS dict), rendered via `st.html()`. Columns are hourly slots 07:00-14:00.

## Testing

Tests are in `tests/test_core.py` covering: staff filtering, LLM response parsing (with/without tags, malformed), constraint validation, and task color mapping. No mocking of external services — tests exercise pure functions only.

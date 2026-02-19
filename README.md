# HK Task Scheduler V2

A Streamlit web app that generates daily housekeeping schedules for a luxury furniture gallery using AI. Upload a staff schedule, select a day, and get a constraint-respecting task assignment displayed as a color-coded timeline grid.

## Features

- **File Upload** — Accept Excel (.xlsx) or CSV staff schedules
- **AI Schedule Generation** — Uses HuggingFace LLM (Llama 3.3 70B Instruct) to produce valid task assignments
- **Multi-Shift Support** — Generates schedules across all 3 shifts (07:00–15:00, 13:00–21:00, 15:00–23:00) in a single call
- **Timeline Grid** — Horizontal grid with employees as rows, hourly slots (07:00–22:00) as columns, color-coded by task category
- **Constraint Validation** — Checks 6 rules: no double-booking, restroom staffing, egress coverage, BOH assignments
- **CSV & PNG Export** — Download generated schedule as CSV or as a PNG screenshot
- **Supabase Persistence** — Uploaded schedules are saved to Supabase for persistence across sessions

## Quick Start

```bash
# Install dependencies
uv sync

# Install Playwright browser (required for PNG export)
uv run playwright install chromium

# Set up environment variables
cp .env.example .env
# Edit .env with your HF_TOKEN (required) and Supabase credentials (optional)

# Run the app
uv run streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | Yes | HuggingFace API token for LLM inference |
| `SUPABASE_URL` | No | Supabase project URL for persistent storage |
| `SUPABASE_API_KEY` | No | Supabase anon key |

For Streamlit Community Cloud, set these in `.streamlit/secrets.toml`.

## How It Works

1. **Upload** — Upload an Excel/CSV with a `Name` column and day-of-week columns containing shift info
2. **Select Day** — Pick a day; the app filters all shifts for that day
3. **Generate** — Click "Generate Schedule" to send staff data to the LLM with gallery-specific constraints
4. **Review** — View the full-day timeline grid (07:00–22:00) and constraint validation results
5. **Export** — Download the schedule as CSV or PNG

## Tech Stack

- **Frontend**: Streamlit
- **AI**: HuggingFace Inference API (Llama 3.3 70B Instruct) via OpenAI SDK
- **Database**: Supabase (optional)
- **PNG Export**: Playwright (headless Chromium)
- **Language**: Python 3.11
- **Package Manager**: uv

## Testing

```bash
uv run pytest
```

## Gallery Layout

The scheduler is designed for a multi-floor luxury gallery:
- **Floors -1, 0, 1**: Furniture showrooms
- **Floor 2**: Restaurant + 4 customer restrooms
- **Floor 3**: Bar
- **Floor 4**: Small restaurant + 2 customer restrooms
- **Floor 5**: Rooftop lounge

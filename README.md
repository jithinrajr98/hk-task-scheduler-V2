# HK Task Scheduler V2

A Streamlit web app that generates daily housekeeping schedules for a luxury furniture gallery using AI. Upload a staff schedule, select a day, and get a constraint-respecting task assignment displayed as a color-coded timeline grid.

## Features

- **File Upload** — Accept Excel (.xlsx) or CSV staff schedules
- **AI Schedule Generation** — Uses Groq LLM (Llama 3.3 70B) to produce valid task assignments
- **Timeline Grid** — Horizontal grid with employees as rows, hourly slots (07:00–14:00) as columns, color-coded by task category
- **Constraint Validation** — Checks 6 rules: no double-booking, restroom staffing, egress coverage, BOH assignments
- **CSV Export** — Download generated schedule as CSV
- **Supabase Persistence** — Uploaded schedules are saved to Supabase for persistence across sessions

## Quick Start

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY (required) and Supabase credentials (optional)

# Run the app
uv run streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key for Groq LLM |
| `SUPABASE_URL` | No | Supabase project URL for persistent storage |
| `SUPABASE_API_KEY` | No | Supabase anon key |

For Streamlit Community Cloud, set these in `.streamlit/secrets.toml`.

## How It Works

1. **Upload** — Upload an Excel/CSV with a `Name` column and day-of-week columns containing shift info
2. **Select Day** — Pick a day; the app filters to Shift 1 (07:00–15:00) staff
3. **Generate** — Click "Generate Schedule" to send staff data to the LLM with gallery-specific constraints
4. **Review** — View the timeline grid and constraint validation results
5. **Export** — Download the schedule as CSV

## Tech Stack

- **Frontend**: Streamlit
- **AI**: Groq API (Llama 3.3 70B Versatile)
- **Database**: Supabase (optional)
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

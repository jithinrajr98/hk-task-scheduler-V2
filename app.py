import json
import io
import os

import pandas as pd
import streamlit as st

from prompt import generate_schedule, parse_response
from supabase_client import push_schedule, load_schedule

# --- Data loading helpers ---

SHIFT_TIME_MAP = {
    "shift_1": {"start_time": "07:00", "end_time": "15:00"},
    "shift_2": {"start_time": "13:00", "end_time": "21:00"},
    "shift_3": {"start_time": "15:00", "end_time": "23:00"},
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TASK_COLORS = {
    "Floor": "#6C9BD2",
    "Outdoor": "#7BC67E",
    "Restroom": "#E8A87C",
    "Egress": "#D4A5D0",
    "BOH": "#F0C75E",
    "Float": "#85E0E0",
    "Break": "#CCCCCC",
}

TIME_SLOTS = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]


def normalize_shift(value):
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    if value == "off":
        return None
    if "7.00" in value or "07" in value:
        return "shift_1"
    if "13.00" in value or "1.00" in value:
        return "shift_2"
    if "15.00" in value or "3.00" in value:
        return "shift_3"
    if "shift 1" in value:
        return "shift_1"
    if "shift 2" in value:
        return "shift_2"
    if "shift 3" in value:
        return "shift_3"
    return None


def parse_uploaded_file(uploaded_file) -> list[dict]:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()
    schedule = []

    for _, row in df.iterrows():
        name = row["Name"]
        for day in df.columns[1:]:
            shift_name = normalize_shift(row[day])
            if shift_name:
                schedule.append({
                    "name": name,
                    "day": day,
                    "shift_name": shift_name,
                    "start_time": SHIFT_TIME_MAP[shift_name]["start_time"],
                    "end_time": SHIFT_TIME_MAP[shift_name]["end_time"],
                })
    return schedule


def load_bundled_schedule() -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "data", "staff_schedule.json")
    with open(path) as f:
        return json.load(f)


def filter_by_day(schedule: list[dict], day: str) -> list[dict]:
    return [s for s in schedule if s["day"] == day]


def get_task_color(task: str) -> str:
    task_lower = task.lower()
    if "boh" in task_lower:
        return TASK_COLORS["BOH"]
    if task_lower == "break":
        return TASK_COLORS["Break"]
    if "floor" in task_lower:
        return TASK_COLORS["Floor"]
    if "outdoor" in task_lower:
        return TASK_COLORS["Outdoor"]
    if "restroom" in task_lower:
        return TASK_COLORS["Restroom"]
    if "egress" in task_lower:
        return TASK_COLORS["Egress"]
    if "float" in task_lower:
        return TASK_COLORS["Float"]
    return "#B0B0B0"


# --- Constraint Validation ---

def validate_constraints(assignments: list[dict]) -> list[dict]:
    results = []

    # Build time->employee->task mapping
    time_map = {}  # {time: {employee: task}}
    for a in assignments:
        for time, task in a["tasks"].items():
            if time not in time_map:
                time_map[time] = {}
            time_map[time][a["employee"]] = task

    # 1. No double-booking
    double_booked = False
    for time, emp_tasks in time_map.items():
        employees = list(emp_tasks.keys())
        if len(employees) != len(set(employees)):
            double_booked = True
            break
    results.append({"rule": "No double-booking", "pass": not double_booked})

    # 2. Restroom_2: 1-2 people, 2 from 14:00
    r2_ok = True
    r2_times = [t for t in time_map if "10:00" <= t <= "22:00"]
    for time in r2_times:
        if time in time_map:
            count = sum(1 for t in time_map[time].values() if "Restroom_2" in t)
            if count < 1:
                r2_ok = False
            if time >= "14:00" and count < 2:
                r2_ok = False
            if count > 2:
                r2_ok = False
    results.append({"rule": "Restroom_2 staffing", "pass": r2_ok})

    # 3. Restroom_4: exactly 1
    r4_ok = True
    r4_times = [t for t in time_map if "10:00" <= t <= "22:00"]
    for time in r4_times:
        if time in time_map:
            count = sum(1 for t in time_map[time].values() if "Restroom_4" in t)
            if count != 1:
                r4_ok = False
    results.append({"rule": "Restroom_4 staffing (exactly 1)", "pass": r4_ok})

    # 4. Egress: exactly 2, 10:00-12:00
    egress_ok = True
    for time in ["10:00", "11:00"]:
        if time in time_map:
            count = sum(1 for t in time_map[time].values() if "Egress" in t)
            if count != 2:
                egress_ok = False
    results.append({"rule": "Egress (exactly 2, 10-12)", "pass": egress_ok})

    # 5. BOH-Breakroom: exactly 1 at 10:00 and 14:00
    boh_br_ok = True
    for time in ["10:00", "14:00"]:
        if time in time_map:
            count = sum(1 for t in time_map[time].values() if "BOH-Breakroom" in t)
            if count != 1:
                boh_br_ok = False
    results.append({"rule": "BOH-Breakroom (exactly 1)", "pass": boh_br_ok})

    # 6. BOH-Restrooms: exactly 1 at 10:00 and 14:00
    boh_rr_ok = True
    for time in ["10:00", "14:00"]:
        if time in time_map:
            count = sum(1 for t in time_map[time].values() if "BOH-Restrooms" in t)
            if count != 1:
                boh_rr_ok = False
    results.append({"rule": "BOH-Restrooms (exactly 1)", "pass": boh_rr_ok})

    return results


# --- Timeline Grid HTML ---

def build_timeline_html(assignments: list[dict]) -> str:
    rows_html = ""
    for idx, a in enumerate(assignments):
        row_bg = "#FFFFFF" if idx % 2 == 0 else "#F8F9FA"
        # Employee name cell
        name = a["employee"]
        initials = "".join(w[0].upper() for w in name.split()[:2])
        cells = ""
        for time in TIME_SLOTS:
            task = a["tasks"].get(time, "")
            if task:
                bg = get_task_color(task)
                cells += (
                    f'<td class="hk-cell">'
                    f'<div class="hk-block" style="background:{bg};">'
                    f'<span class="hk-task-text">{task}</span>'
                    f'</div></td>'
                )
            else:
                cells += '<td class="hk-cell"><div class="hk-empty"></div></td>'

        rows_html += (
            f'<tr style="background:{row_bg};">'
            f'<td class="hk-name-cell">'
            f'<div class="hk-name-row">'
            f'<span class="hk-initials">{initials}</span>'
            f'<span class="hk-name">{name}</span>'
            f'</div></td>'
            f'{cells}</tr>'
        )

    header_cells = "".join(
        f'<th class="hk-th">{t}</th>' for t in TIME_SLOTS
    )

    legend_items = "".join(
        f'<div class="hk-legend-item">'
        f'<span class="hk-legend-swatch" style="background:{color};"></span>'
        f'<span class="hk-legend-label">{cat}</span>'
        f'</div>'
        for cat, color in TASK_COLORS.items()
    )

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,300&display=swap');

        .hk-grid-wrap {{
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 100%;
            overflow-x: auto;
            color: #1A1A2E;
        }}

        /* ── Legend ── */
        .hk-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 16px;
            padding: 10px 14px;
            background: #F1F3F5;
            border-radius: 8px;
            border: 1px solid #E2E6EA;
        }}
        .hk-legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px 3px 6px;
            background: #FFFFFF;
            border-radius: 100px;
            border: 1px solid #E2E6EA;
        }}
        .hk-legend-swatch {{
            width: 10px;
            height: 10px;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        .hk-legend-label {{
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.02em;
            color: #495057;
        }}

        /* ── Table ── */
        .hk-table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #DEE2E6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
        }}

        .hk-th {{
            padding: 10px 8px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            text-align: center;
            color: #868E96;
            background: #F8F9FA;
            border-bottom: 2px solid #DEE2E6;
            min-width: 100px;
        }}
        .hk-th:first-child {{
            text-align: left;
            padding-left: 16px;
            min-width: 180px;
        }}

        /* ── Name cell ── */
        .hk-name-cell {{
            padding: 8px 12px 8px 16px;
            border-bottom: 1px solid #ECEEF0;
            vertical-align: middle;
        }}
        .hk-name-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .hk-initials {{
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: #E9ECEF;
            color: #495057;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.04em;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .hk-name {{
            font-size: 13px;
            font-weight: 500;
            color: #212529;
            white-space: nowrap;
        }}

        /* ── Task cells ── */
        .hk-cell {{
            padding: 4px 3px;
            border-bottom: 1px solid #ECEEF0;
            border-left: 1px solid #F1F3F5;
            vertical-align: middle;
            text-align: center;
        }}
        .hk-block {{
            padding: 7px 6px;
            border-radius: 5px;
            min-height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s ease, box-shadow 0.1s ease;
        }}
        .hk-block:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }}
        .hk-task-text {{
            font-size: 11px;
            font-weight: 600;
            color: rgba(0,0,0,0.7);
            letter-spacing: 0.01em;
            white-space: nowrap;
            line-height: 1.2;
        }}
        .hk-empty {{
            min-height: 32px;
            border-radius: 5px;
            background: repeating-linear-gradient(
                -45deg,
                transparent,
                transparent 3px,
                #F1F3F5 3px,
                #F1F3F5 4px
            );
        }}

        /* ── Row hover ── */
        .hk-table tbody tr:hover {{
            background: #F0F4FF !important;
        }}
        .hk-table tbody tr:hover .hk-initials {{
            background: #D0D7DE;
        }}

        /* ── Last row no border ── */
        .hk-table tbody tr:last-child td {{
            border-bottom: none;
        }}
    </style>

    <div class="hk-grid-wrap">
        <div class="hk-legend">{legend_items}</div>
        <table class="hk-table">
            <thead>
                <tr>
                    <th class="hk-th">Employee</th>
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return html


# --- Export ---

def assignments_to_csv(assignments: list[dict]) -> str:
    rows = []
    for a in assignments:
        for time, task in a["tasks"].items():
            rows.append({"Employee": a["employee"], "Time": time, "Task": task})
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


# --- Streamlit App ---

def main():
    st.set_page_config(page_title="HK Task Scheduler", layout="wide")
    st.title("HK Task Scheduler")
    st.caption("Daily housekeeping schedule generator for luxury gallery")

    # Sidebar: Upload + Day Selection
    with st.sidebar:
        st.header("Schedule Input")

        uploaded_file = st.file_uploader(
            "Upload staff schedule", type=["xlsx", "csv"],
            help="Excel or CSV with Name column + day columns"
        )

        if uploaded_file:
            try:
                schedule = parse_uploaded_file(uploaded_file)
                st.success(f"Loaded {len(schedule)} schedule entries")
                try:
                    push_schedule(schedule)
                    st.success("Saved to Supabase")
                except Exception as e:
                    st.warning(f"Could not save to Supabase: {e}")
            except Exception as e:
                st.error(f"Error parsing file: {e}")
                schedule = None
        else:
            # Try Supabase first, fall back to bundled JSON
            schedule = None
            try:
                schedule = load_schedule()
            except Exception:
                pass
            if schedule:
                st.info("Loaded schedule from Supabase")
            else:
                schedule = load_bundled_schedule()
                st.info("Using bundled schedule data")

        day = st.selectbox("Select day", DAYS, index=3)  # Default Thursday

        if schedule:
            day_staff = filter_by_day(schedule, day)
            st.metric("Available staff", len(day_staff))

            if len(day_staff) < 6:
                st.warning(f"Only {len(day_staff)} staff available. Minimum 6 recommended.")
        else:
            day_staff = []

    # Main area
    if not schedule:
        st.info("Please upload a valid staff schedule file.")
        return

    if not day_staff:
        st.warning(f"No staff available on {day}.")
        return

    # Generate button
    col1, col2 = st.columns([1, 1])
    with col1:
        generate = st.button("Generate Schedule", type="primary", use_container_width=True)
    with col2:
        regenerate = st.button("Regenerate", use_container_width=True)

    if generate or regenerate:
        with st.spinner("Generating schedule with AI..."):
            try:
                result, raw_response = generate_schedule(day_staff)
                if result and "assignments" in result:
                    st.session_state["schedule_result"] = result
                    st.session_state["day_staff"] = day_staff
                else:
                    st.error("Failed to parse schedule from AI response. Try regenerating.")
                    with st.expander("Raw LLM response (debug)"):
                        st.code(raw_response[:3000])
            except Exception as e:
                st.error(f"Generation failed: {e}")

    # Display results
    if "schedule_result" in st.session_state:
        result = st.session_state["schedule_result"]
        assignments = result["assignments"]
        assignments = sorted(assignments, key=lambda a: min(a["tasks"].keys()))

        st.subheader(f"Schedule for {day}")
        st.html(build_timeline_html(assignments))

        # Constraint validation
        st.subheader("Constraint Validation")
        validations = validate_constraints(assignments)
        cols = st.columns(3)
        for i, v in enumerate(validations):
            with cols[i % 3]:
                icon = "✅" if v["pass"] else "❌"
                st.markdown(f"{icon} **{v['rule']}**")

        # Export
        csv_data = assignments_to_csv(assignments)
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"schedule_{day.lower()}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()

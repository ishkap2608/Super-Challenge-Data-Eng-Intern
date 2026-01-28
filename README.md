# Event Sessions Builder

**Solution to Super.com Data Engineering Intern OA Challenge**

⚠️ **Not to be used or distributed elsewhere without permission.**

A data pipeline that validates event data, removes duplicates, and creates per-user session summaries.

🔗 **Live Demo**: [https://super-challenge-data-eng-interngit-sgynk94zfjsibdfhyq2d8k.streamlit.app/](https://super-challenge-data-eng-interngit-sgynk94zfjsibdfhyq2d8k.streamlit.app/)

## Setup

```bash
pip install pandas streamlit
```

## Usage

**CLI:**
```bash
python main.py --input events.json --out sessions.csv --skips_out skipped.csv
```

**Web UI:**
```bash
streamlit run app.py
```

## How It Works

1. **Parse JSON** - Extracts event objects (handles multi-line JSON)
2. **Validate** - Checks JSON syntax, required fields, and ISO-8601 timestamps
3. **Deduplicate** - Removes exact duplicates by user_id, event_time, event_type
4. **Aggregate** - Groups events by user to create session summaries

Invalid events are logged with reasons for audit.

## Project Structure

```
├── app.py              # Streamlit web interface
├── main.py             # CLI entry point
├── src/processor.py    # Core processing logic
├── events.json         # Sample data
└── requirements.txt
```

## Streamlit App

**Metrics** - Real-time stats on total events, valid events, skipped, duplicates removed, unique users

**Sessions Tab** - Per-user session summaries with start time, end time, event count. Download as CSV.

**Skipped Rows Tab** - Events that failed validation with reasons. View breakdown by error type.

**Events Tab** - Deduplicated events with user filter and 5-minute trend chart by event type.

**Original Data Tab** - View raw JSON input and download.

## Output Files

- `sessions.csv` - Session summaries (user_id, session_start, session_end, event_count)
- `skipped.csv` - Events that failed validation with error reasons

## Example

**Input:**
```json
{"user_id": 1, "event_time": "2024-07-10T10:00:00Z", "event_type": "login"}
{"user_id": 1, "event_time": "2024-07-10T10:05:00Z", "event_type": "view"}
{"user_id": 1, "event_time": "2024-07-10T10:05:00Z", "event_type": "view"}
{"user_id": 2, "event_time": "invalid-timestamp", "event_type": "click"}
{"user_id": 2, "event_time": "2024-07-10T10:10:00Z", "event_type": "purchase"}
```

**Output (sessions.csv):**
```
user_id,session_start,session_end,event_count
1,2024-07-10T10:00:00Z,2024-07-10T10:05:00Z,2
2,2024-07-10T10:10:00Z,2024-07-10T10:10:00Z,1
```

**Output (skipped.csv):**
```
event,reason,user_id,event_time,event_type
4,invalid ISO-8601,2,invalid-timestamp,click
```

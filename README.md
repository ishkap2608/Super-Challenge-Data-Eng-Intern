# Event Sessions Builder

A data engineering pipeline that processes user event data, validates timestamps, removes duplicates, and generates per-user session summaries. This project combines a robust backend processor with an interactive Streamlit dashboard for real-time data exploration.

🔗 **Live Demo**: [https://super-challenge-data-eng-interngit-sgynk94zfjsibdfhyq2d8k.streamlit.app/](https://super-challenge-data-eng-interngit-sgynk94zfjsibdfhyq2d8k.streamlit.app/)

---

## 📋 Table of Contents
- [Overview](#overview)
- [Methodology](#methodology)
- [Project Structure](#project-structure)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Streamlit App Features](#streamlit-app-features)
- [Data Flow](#data-flow)

---

## Overview

The **Event Sessions Builder** is a data processing application designed to:
- Parse and validate JSON event data from users
- Handle malformed or invalid records gracefully
- Identify and remove duplicate events
- Generate meaningful session summaries for each user

This solution addresses the real-world challenge of working with messy, unstructured event data where timestamps may be malformed, fields might be missing, or exact duplicates need to be consolidated.

---

## Methodology

### Approach

The project follows a **robust ETL (Extract, Transform, Load)** pattern with comprehensive error handling:

#### 1. **Extraction Phase**
- **Content Parsing**: The system extracts JSON objects from the input using a state machine approach (tracking brace depth) rather than naive line-by-line parsing
- **Rationale**: This handles cases where JSON objects may span multiple lines or are not in strict JSONL format
- **Event Indexing**: Each event is numbered sequentially for tracking purposes

#### 2. **Validation Phase**
The system validates data at multiple layers:
- **JSON Syntax**: Attempts to parse each event as valid JSON
- **Schema Validation**: Ensures required fields exist: `user_id`, `event_time`, `event_type`
- **Timestamp Parsing**: Validates ISO-8601 formatted timestamps with these rules:
  - Normalizes `Z` suffix to `+00:00` for compatibility
  - Accepts timezone-aware datetimes
  - Defaults naive timestamps to UTC timezone

**Skipped Events**: Any events failing validation are logged with the reason (e.g., `invalid_ISO-8601`, `missing_key_or_bad_schema`, `json_decode_error`) for audit purposes.

#### 3. **Deduplication Phase**
- **Exact Duplicate Removal**: Removes records with identical `user_id`, `event_time`, and `event_type`
- **Rationale**: Exact duplicates often occur from retries or data replication errors
- **Strategy**: Uses pandas `drop_duplicates()` with `keep="first"` to preserve temporal order

#### 4. **Aggregation Phase**
- **Per-User Sessions**: Groups events by `user_id` and computes:
  - `session_start`: Earliest event timestamp for the user
  - `session_end`: Latest event timestamp for the user
  - `event_count`: Total valid events in the session
- **Output Format**: Timestamps are converted to ISO-8601 format for portability

#### 5. **Statistics Tracking**
Every run produces comprehensive metrics:
- Total events processed
- Valid events retained
- Events skipped with reasons
- Duplicates removed
- Unique users in dataset

---

## Project Structure

```
Super-Challenge-Data-Eng-Intern/
├── app.py                    # Streamlit web application
├── main.py                   # CLI entry point for batch processing
├── src/
│   ├── __init__.py           # Package marker
│   └── processor.py          # Core processing logic
├── events.json               # Sample event data
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Key Components

#### `src/processor.py` - Core Processing Engine
**Classes & Functions:**
- `ProcessResult`: Dataclass containing output DataFrames and statistics
- `_parse_iso8601()`: Robust ISO-8601 timestamp parser with timezone handling
- `_extract_events_from_content()`: State machine parser for flexible JSON extraction
- `process_file()`: Main processing pipeline (accepts file-like objects)
- `process_path()`: File-based wrapper for CLI usage

**Key Features:**
- Robust error handling with detailed logging
- Type-safe dataclass output structure
- Reusable components for both CLI and web application

#### `app.py` - Streamlit Dashboard
Interactive web interface featuring:
- File upload for custom event data
- Real-time metric visualization
- Multi-tab interface for data exploration
- CSV download capability

#### `main.py` - CLI Interface
Command-line tool for batch processing:
```bash
python main.py --input events.json --out sessions.csv --skips_out skipped.csv
```

---

## Features

### Data Processing
✅ **Flexible JSON Parsing** - Handles malformed or multi-line JSON  
✅ **Comprehensive Validation** - Schema, type, and timestamp checks  
✅ **Detailed Error Tracking** - Every skipped row logged with reason  
✅ **Exact Duplicate Removal** - Intelligent deduplication strategy  
✅ **Session Aggregation** - Per-user event summaries with time bounds  

### Output Formats
✅ **CSV Export** - Session summaries and error logs  
✅ **Statistics** - Real-time metrics dashboard  
✅ **Audit Trail** - Complete skipped records with reasons  

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ishkap2608/Super-Challenge-Data-Eng-Intern.git
   cd Super-Challenge-Data-Eng-Intern
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install pandas streamlit
   ```

### Dependencies
- **pandas** - Data manipulation and aggregation
- **streamlit** - Web application framework

---

## Usage

### Option 1: Command-Line Interface (CLI)

Process events from a JSON file and output session summaries:

```bash
python main.py --input events.json --out sessions.csv --skips_out skipped.csv
```

**Output:**
- `sessions.csv` - Per-user session summary
- `skipped.csv` - Events that failed validation with reasons
- Console statistics

### Option 2: Streamlit Web App

Launch the interactive dashboard:

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## Streamlit App Features

### 1. **File Upload**
- Drag-and-drop or click to upload `events.json` file
- Supports both standard JSON and JSON Lines formats
- Sample data available for quick testing

### 2. **Metrics Dashboard**
The top of the page displays five key performance indicators in real-time:

| Metric | Description |
|--------|-------------|
| **Total Events** | Count of all events in the input file |
| **Valid Events** | Events that passed all validation checks |
| **Skipped** | Events rejected due to validation failures |
| **Dupes Removed** | Exact duplicates eliminated during deduplication |
| **Unique Users** | Number of distinct user_id values after deduplication |

### 3. **Sessions Tab**
**Purpose**: View aggregated user session data

**Data Displayed:**
- `user_id` - User identifier
- `session_start` - ISO-8601 timestamp of first event
- `session_end` - ISO-8601 timestamp of last event  
- `event_count` - Total events in user's session

**Actions:**
- View full table with scrolling
- Download `sessions.csv` for further analysis
- Sort by clicking column headers

### 4. **Skipped Rows Tab**
**Purpose**: Audit and understand data quality issues

**Data Displayed:**
- `event` - Event sequence number in the file
- `reason` - Human-readable error message (e.g., `invalid ISO-8601`, `missing_key_or_bad_schema`)
- `raw` - First 300 characters of problematic event (for context)
- Additional fields if available: `user_id`, `event_time`, `event_type`

**Visualization:**
- Table of all skipped events
- Breakdown chart showing count by reason
- Download `skipped.csv` for error analysis

### 5. **Events Tab**
**Purpose**: Explore validated, deduplicated events

**Features:**
- **User Filter**: Select individual user or view all
- **Sorted by Time**: Events displayed chronologically
- **Trend Chart**: 5-minute bucketed line chart showing event volume by type
- **Interactive**: Filter dynamically without reprocessing

### 6. **Original Data Tab**
**Purpose**: Verify input integrity

**Features:**
- View raw uploaded JSON with syntax highlighting
- Download original file for archiving
- Helpful for debugging parsing issues

---

## Data Flow

### Processing Pipeline

```
┌─────────────────────────────────┐
│  Input: events.json             │
│  (JSON or JSON Lines format)    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  1. EXTRACTION                  │
│  - Parse content as string      │
│  - Extract JSON objects via     │
│    state machine (brace tracking)
│  - Index each event sequentially
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  2. VALIDATION                  │
│  - JSON syntax check            │
│  - Schema validation            │
│    (user_id, event_time,        │
│     event_type required)        │
│  - ISO-8601 timestamp parsing   │
│  - Timezone normalization       │
└──────────────┬──────────────────┘
               │
         ┌─────┴──────┐
         │             │
         ▼             ▼
    ✓ Valid       ✗ Invalid
    Events       Events
         │             │
         │             └──→ Skipped DataFrame
         │                  (with reasons)
         │
         ▼
┌─────────────────────────────────┐
│  3. DEDUPLICATION               │
│  - Remove exact duplicates      │
│  - Keep first occurrence        │
│  - Track count removed          │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  4. AGGREGATION                 │
│  - Group by user_id             │
│  - Calculate session bounds:    │
│    • Min(event_time) →          │
│      session_start              │
│    • Max(event_time) →          │
│      session_end                │
│    • Count(events) →            │
│      event_count                │
└──────────────┬──────────────────┘
               │
         ┌─────┴────────┬─────────┐
         │              │         │
         ▼              ▼         ▼
    Sessions       Events      Stats
    DataFrame      DataFrame   Dictionary
         │              │         │
         └──────────────┼─────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │  ProcessResult       │
              │  (consolidated)      │
              └──────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    CSV Export    Dashboard    Console
    (batch)       (interactive) Output
```

### Example Data Flow

**Input Event:**
```json
{"user_id": 12, "event_time": "2024-07-10T11:45:00Z", "event_type": "view"}
```

**Processing Steps:**
1. ✅ Extracted as valid JSON object
2. ✅ Schema validated (all fields present)
3. ✅ Timestamp parsed: `2024-07-10T11:45:00Z` → `datetime(2024, 7, 10, 11, 45, 0, tzinfo=UTC)`
4. ✅ Event added to valid events list
5. ✅ Included in session aggregation for `user_id=12`

**Output (Session Summary):**
```csv
user_id,session_start,session_end,event_count
12,2024-07-10T11:45:00Z,2024-07-10T12:30:45Z,42
```

---

## Example Workflow

### Step 1: Prepare Data
Create `events.json`:
```json
{"user_id": 1, "event_time": "2024-07-10T10:00:00Z", "event_type": "login"}
{"user_id": 1, "event_time": "2024-07-10T10:05:00Z", "event_type": "view"}
{"user_id": 1, "event_time": "2024-07-10T10:05:00Z", "event_type": "view"}
{"user_id": 2, "event_time": "invalid-timestamp", "event_type": "click"}
{"user_id": 2, "event_time": "2024-07-10T10:10:00Z", "event_type": "purchase"}
```

### Step 2: Run Processing
```bash
python main.py --input events.json --out sessions.csv --skips_out skipped.csv
```

### Step 3: Inspect Results

**sessions.csv:**
```
user_id,session_start,session_end,event_count
1,2024-07-10T10:00:00Z,2024-07-10T10:05:00Z,2
2,2024-07-10T10:10:00Z,2024-07-10T10:10:00Z,1
```

**skipped.csv:**
```
event,reason,user_id,event_time,event_type
4,invalid ISO-8601: time data 'invalid-timestamp' does not match any format,2,invalid-timestamp,click
```

**Console Output:**
```
Done.
total_events: 5
valid_events: 4
skipped_events: 1
duplicates_removed: 1
unique_users: 2
```

---

## Key Highlights

### Robustness
- **Graceful Degradation**: Invalid records skip without halting the pipeline
- **Detailed Logging**: Every error captures the problematic data and reason
- **Timezone Handling**: Automatically normalizes timezone formats for consistency

### Performance
- **Single Pass Processing**: Events processed once with O(n) complexity
- **Efficient Deduplication**: Uses pandas' optimized drop_duplicates
- **Memory Efficient**: Streams data processing without loading entire dataset in memory

### Usability
- **Dual Interface**: CLI for automation, Streamlit for exploration
- **Interactive Dashboard**: Real-time filtering and visualization
- **CSV Export**: Easily integrate results with other tools

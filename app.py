import io
import streamlit as st
import pandas as pd

from src.processor import process_file

st.set_page_config(page_title="Event Sessions", layout="wide")

st.title("Event Sessions Builder")
st.caption("Validate timestamps → drop exact duplicates → compute per-user sessions")

uploaded = st.file_uploader("Upload events.json (JSON Lines)", type=["json", "txt"])

use_sample = st.checkbox("Use small sample if no file uploaded", value=not bool(uploaded))

sample = b"""
{"user_id": 12, "event_time": "2024-07-10T11:45:00Z", "event_type": "view"}
{"user_id": 13, "event_time": "2024-07-10T11:59:30Z", "event_type": "view"}
{"user_id": 12, "event_time": "bad-timestamp", "event_type": "click"}
{"user_id": 12, "event_time": "2024-07-10T11:45:00Z", "event_type": "view"}
{"user_id": 13, "event_time": "2024-07-11T10:40:00Z", "event_type": "purchase"}
""".strip()

if uploaded:
    raw_bytes = uploaded.getvalue()
elif use_sample:
    raw_bytes = sample
else:
    st.stop()

res = process_file(io.BytesIO(raw_bytes))
stats = res.stats

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total events", stats.get("total_events", 0))
c2.metric("Valid events", stats.get("valid_events", 0))
c3.metric("Skipped", stats.get("skipped_events", 0))
c4.metric("Dupes removed", stats.get("duplicates_removed", 0))
c5.metric("Unique users", stats.get("unique_users", 0))

tab1, tab2, tab3, tab4 = st.tabs(["Sessions", "Skipped rows", "Events", "Original Data"])

with tab1:
    st.subheader("Per-user session summary")
    if res.sessions_df.empty:
        st.info("No sessions to display.")
    else:
        st.dataframe(res.sessions_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download sessions.csv",
            data=res.sessions_df.to_csv(index=False).encode("utf-8"),
            file_name="sessions.csv",
            mime="text/csv",
        )

with tab2:
    st.subheader("Skipped lines (with reason)")
    if res.skipped_df.empty:
        st.success("No skipped lines 🎉")
    else:
        st.dataframe(res.skipped_df, use_container_width=True, hide_index=True)

        reason_counts = res.skipped_df["reason"].value_counts().reset_index()
        reason_counts.columns = ["reason", "count"]
        st.write("Reason counts")
        st.dataframe(reason_counts, use_container_width=True, hide_index=True)

        st.download_button(
            "Download skipped.csv",
            data=res.skipped_df.to_csv(index=False).encode("utf-8"),
            file_name="skipped.csv",
            mime="text/csv",
        )

with tab3:
    st.subheader("Events (deduped)")
    if res.events_df.empty:
        st.info("No valid events.")
    else:
        df = res.events_df.copy()
        df["event_time"] = pd.to_datetime(df["event_time"], utc=True)

        users = ["(all)"] + sorted(df["user_id"].unique().tolist())
        chosen = st.selectbox("Filter by user_id", users)

        if chosen != "(all)":
            df = df[df["user_id"] == chosen]

        st.dataframe(df.sort_values("event_time"), use_container_width=True, hide_index=True)

        # quick trend chart
        tmp = df.set_index("event_time")
        series = tmp.groupby("event_type").resample("5min").size().unstack(0).fillna(0)
        st.line_chart(series)

with tab4:
    st.subheader("Original Uploaded Data")
    try:
        original_text = raw_bytes.decode("utf-8", errors="replace")
        st.code(original_text, language="json")
        st.download_button(
            "Download original file",
            data=raw_bytes,
            file_name="original_events.json",
            mime="application/json",
        )
    except Exception as e:
        st.error(f"Could not display original data: {e}")

import streamlit as st
from calender_connection import authenticate_google
from datetime import datetime
import pytz

st.title("📅 Smart Timetable AI")

# Authenticate once
service = authenticate_google()
st.success("✅ Connected to Google Calendar!")

TIMEZONE = pytz.timezone("Asia/Kolkata")

# ------------------------------
# FUNCTION: GET EVENTS FOR A DATE
# ------------------------------
def get_events_for_date(selected_date):
    start_of_day = TIMEZONE.localize(
        datetime.combine(selected_date, datetime.min.time())
    )
    end_of_day = TIMEZONE.localize(
        datetime.combine(selected_date, datetime.max.time())
    )

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return events_result.get("items", [])

# ------------------------------
# FUNCTION: CHECK CONFLICT
# ------------------------------
def has_conflict(new_start, new_end, events):
    for event in events:
        if "dateTime" not in event["start"]:
            continue

        existing_start = datetime.fromisoformat(event["start"]["dateTime"])
        existing_end = datetime.fromisoformat(event["end"]["dateTime"])

        if new_start < existing_end and new_end > existing_start:
            return True
    return False

# ------------------------------
# SHOW UPCOMING EVENTS
# ------------------------------
st.subheader("📌 Upcoming Events")

if st.button("Show Upcoming Events"):
    now = datetime.utcnow().isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    if not events:
        st.info("No upcoming events.")
    else:
        for event in events:
            st.write("•", event.get("summary", "No title"))

# ------------------------------
# CREATE NEW EVENT FORM (TWO COLUMNS + PRIORITY)
# ------------------------------
st.subheader("➕ Create New Event")

col1, col2 = st.columns(2)

with col1:
    title = st.text_input("Event Title")
    date = st.date_input("Select Date")

with col2:
    start_time = st.time_input("Start Time")
    end_time = st.time_input("End Time")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

if st.button("Create Event"):
    if not title:
        st.error("Please enter an event title.")
    elif start_time >= end_time:
        st.error("End time must be after start time.")
    else:
        new_start = TIMEZONE.localize(datetime.combine(date, start_time))
        new_end = TIMEZONE.localize(datetime.combine(date, end_time))

        events = get_events_for_date(date)

        if has_conflict(new_start, new_end, events):
            st.error("⚠️ Time conflict detected! Event not created.")
        else:
            event = {
                "summary": title,
                "description": f"Priority: {priority}",
                "start": {
                    "dateTime": new_start.isoformat(),
                    "timeZone": "Asia/Kolkata",
                },
                "end": {
                    "dateTime": new_end.isoformat(),
                    "timeZone": "Asia/Kolkata",
                },
            }

            service.events().insert(
                calendarId="primary",
                body=event
            ).execute()

            st.success(f"✅ Event Created Successfully! (Priority: {priority})")
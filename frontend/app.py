import streamlit as st
import requests
import datetime
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="TimeCapsule Frontend", layout="centered")
st.title("TimeCapsule")

if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

def safe_request(method, url, **kwargs):
    try:
        if method.upper() == 'GET':
            return requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            return requests.post(url, **kwargs)
        elif method.upper() == 'PATCH':
            return requests.patch(url, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("Can't reach the server — make sure the Django backend is running on localhost:8000")
        return None

# 1. Login Screen
if not st.session_state["access_token"]:
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log in")
        if submit:
            resp = safe_request("POST", f"{API_URL}/api/token/", json={"username": username, "password": password})
            if resp:
                if resp.status_code == 200:
                    st.session_state["access_token"] = resp.json().get("access")
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    st.stop()

# Helpers
def get_headers():
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}

def handle_unauthorized(response):
    if response and response.status_code == 401:
        st.session_state["access_token"] = None
        st.error("Session expired or unauthorized. Please log in again.")
        st.rerun()
        return True
    return False

# 2. Main Interface (Logged In)
st.button("Log Out", on_click=lambda: st.session_state.update({"access_token": None}))

# NOTIFICATIONS
notif_resp = safe_request("GET", f"{API_URL}/api/notifications/", headers=get_headers(), params={"unread_only": "true"})
if notif_resp and not handle_unauthorized(notif_resp):
    if notif_resp.status_code == 200:
        unreads = notif_resp.json()
        if unreads:
            st.info(f"🔔 {len(unreads)} new capsule(s) unlocked!")
            with st.expander("View Notifications"):
                for n in unreads:
                    st.write(f"- {n.get('message')}")
                if st.button("Mark all as read"):
                    for n in unreads:
                        safe_request("PATCH", f"{API_URL}/api/notifications/{n['id']}/", headers=get_headers(), json={"is_read": True})
                    st.rerun()

tab0, tab1, tab2, tab3 = st.tabs(["My Capsules", "Write a Capsule", "Reflect", "Search & Mood Trends"])

with tab0:
    st.header("My Capsules")
    filter_opt = st.radio("Filter", ["All", "Unlocked only", "Locked only"], horizontal=True)
    
    capsules_resp = safe_request("GET", f"{API_URL}/api/capsules/", headers=get_headers(), params={"include_locked": "true"})
    if capsules_resp and not handle_unauthorized(capsules_resp):
        if capsules_resp.status_code == 200:
            capsules = capsules_resp.json()
            if not capsules:
                st.write("You haven't written any capsules yet — head to 'Write a Capsule' to start.")
            else:
                # Sort most recent first based on created_at
                capsules.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                for cap in capsules:
                    is_unlocked = cap.get('is_unlocked', False)
                    if filter_opt == "Unlocked only" and not is_unlocked:
                        continue
                    if filter_opt == "Locked only" and is_unlocked:
                        continue
                        
                    with st.container():
                        st.write(f"### {cap.get('title')} [{cap.get('mood')}]")
                        st.write(f"*Created on {cap.get('created_at')[:10]}*")
                        
                        if is_unlocked:
                            content = cap.get('content', '')
                            preview = content[:150] + ("..." if len(content) > 150 else "")
                            st.write(f"_{preview}_")
                            st.caption(f"Unlocked on {cap.get('unlock_date')[:10]}")
                        else:
                            unlock_str = cap.get('unlock_date')[:10]
                            unlock_dt = datetime.datetime.fromisoformat(cap.get('unlock_date').replace("Z", "+00:00"))
                            now_dt = datetime.datetime.now(datetime.timezone.utc)
                            delta = unlock_dt - now_dt
                            days = delta.days
                            if days > 0:
                                countdown = f"Unlocks in {days} days"
                            else:
                                countdown = "Unlocking soon..."
                            st.write(f"🔒 Locked until {unlock_str} ({countdown})")
                        st.divider()

with tab1:
    st.header("Write a Capsule")
    with st.form("capsule_form"):
        title = st.text_input("Title")
        content = st.text_area("Content")
        mood = st.selectbox("Mood", ["happy", "sad", "stressed", "motivated", "anxious", "calm", "nostalgic"])
        unlock_date = st.date_input("Unlock Date", min_value=datetime.date.today())
        
        submit_capsule = st.form_submit_button("Save Capsule")
        if submit_capsule:
            data = {
                "title": title,
                "content": content,
                "mood": mood,
                "unlock_date": unlock_date.isoformat()
            }
            with st.spinner("Saving your capsule..."):
                resp = safe_request("POST", f"{API_URL}/api/capsules/", headers=get_headers(), json=data)
            if resp and not handle_unauthorized(resp):
                if resp.status_code == 201:
                    st.success(f"Capsule created! It will unlock on {unlock_date.isoformat()}.")
                else:
                    st.error(f"Failed to create capsule: {resp.text}")

with tab2:
    st.header("Reflect")
    question = st.text_input("Ask a question about your past entries:")
    if st.button("Reflect"):
        if question:
            with st.spinner("Reflecting on your past entries..."):
                resp = safe_request("POST", f"{API_URL}/api/capsules/reflect/", headers=get_headers(), json={"question": question})
            if resp and not handle_unauthorized(resp):
                if resp.status_code == 200:
                    data = resp.json()
                    st.write("### Reflection")
                    st.info(data.get("reflection", ""))
                    
                    ref_ids = data.get("referenced_capsules", [])
                    if ref_ids:
                        with st.expander("Capsules referenced"):
                            for cid in ref_ids:
                                cap_resp = safe_request("GET", f"{API_URL}/api/capsules/{cid}/", headers=get_headers())
                                if cap_resp and cap_resp.status_code == 200:
                                    cap_data = cap_resp.json()
                                    st.write(f"**{cap_data.get('title')}** ({cap_data.get('created_at')[:10]}) - Mood: {cap_data.get('mood')}")
                                else:
                                    st.write(f"Capsule ID: {cid}")
                else:
                    st.error(f"Reflection failed: {resp.text}")
        else:
            st.warning("Please enter a question.")

with tab3:
    st.header("Search & Mood Trends")
    
    st.subheader("Search")
    search_query = st.text_input("Search your unlocked capsules:")
    if st.button("Search"):
        if search_query:
            with st.spinner("Searching your memories..."):
                resp = safe_request("GET", f"{API_URL}/api/capsules/search/", headers=get_headers(), params={"q": search_query})
            if resp and not handle_unauthorized(resp):
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        for r in results:
                            with st.container():
                                st.write(f"**{r.get('title')}** | {r.get('created_at')[:10]} | {r.get('mood')}")
                                st.write(f"_{r.get('content')[:100]}..._")
                                st.divider()
                    else:
                        st.write("No results found.")
                else:
                    st.error(f"Search failed: {resp.text}")
                    
    st.subheader("Mood Trends")
    if st.button("Load Trends"):
        with st.spinner("Loading your mood history..."):
            resp = safe_request("GET", f"{API_URL}/api/capsules/mood-trends/", headers=get_headers())
        if resp and not handle_unauthorized(resp):
            if resp.status_code == 200:
                trends_data = resp.json()
                if trends_data:
                    df_data = []
                    for month, moods in trends_data.items():
                        for mood, count in moods.items():
                            df_data.append({"Month": month, "Mood": mood, "Count": count})
                    
                    df = pd.DataFrame(df_data)
                    if not df.empty:
                        df_pivot = df.pivot(index="Month", columns="Mood", values="Count").fillna(0)
                        st.bar_chart(df_pivot)
                    else:
                        st.write("No mood data available.")
                else:
                    st.write("No trends data found.")
            else:
                st.error(f"Failed to load trends: {resp.text}")

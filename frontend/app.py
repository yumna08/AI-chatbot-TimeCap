import streamlit as st
import requests
import datetime
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="TimeCapsule",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL DARK THEME CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [data-testid="stApp"] {
    background-color: #0d0d0d;
    color: #e8e8e8;
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif;
}

/* ── Main area buttons (default primary look) ── */
[data-testid="stApp"] .stButton > button {
    background-color: #ffffff !important;
    color: #0d0d0d !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.1rem !important;
    border: none !important;
    transition: opacity 0.15s !important;
}
[data-testid="stApp"] .stButton > button:hover {
    opacity: 0.92 !important;
}

/* ── Nav buttons in sidebar (override for sidebar) ── */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    color: #aaaaaa;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    font-size: 0.92rem;
    font-weight: 400;
    transition: background 0.15s, color 0.15s;
    margin-bottom: 2px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.07);
    color: #ffffff;
}

/* ── Active nav item (rendered as markup) ── */
.active-nav {
    width: 100%;
    display: block;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
    color: #ffffff;
    font-weight: 600;
    margin-bottom: 4px;
}

/* ── Inputs / Textareas / Selects ── */
input, textarea, select,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #1a1a1a !important;
    color: #e8e8e8 !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
}

/* ── Card wrapper (applied via st.container + CSS class via markdown) ── */
.tc-card {
    background: #1a1a1a;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

/* ── Mood badge ── */
.mood-badge {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #cccccc;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Lock badge ── */
.lock-badge {
    display: inline-block;
    background: rgba(220,80,60,0.15);
    border: 1px solid rgba(220,80,60,0.25);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #f47a6e;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Unlock badge ── */
.unlock-badge {
    display: inline-block;
    background: rgba(60,180,100,0.15);
    border: 1px solid rgba(60,180,100,0.25);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #6dd98c;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
}
[data-testid="stChatMessage"][data-role="user"] {
    background-color: rgba(30,58,95,0.18);
}
[data-testid="stChatMessage"][data-role="assistant"] {
    background-color: rgba(26,26,46,0.22);
}

/* ── File uploader / dropzone styling ── */
[data-testid="stFileUploader"] {
    background: linear-gradient(180deg,#141414,#111111);
    border: 2px dashed rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    color: #ddd;
}
[data-testid="stFileUploader"] .stMarkdown p {
    color: #bdbdbd;
    margin: 0.4rem 0 0 0;
}

/* ── Page headings ── */
h1, h2, h3 {
    color: #ffffff;
    font-weight: 600;
}

/* ── Dividers ── */
hr {
    border-color: rgba(255,255,255,0.07);
}

/* ── Info / success banners ── */
[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0d0d; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
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

def get_headers():
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}

def handle_unauthorized(response):
    if response and response.status_code == 401:
        st.session_state["access_token"] = None
        st.error("Session expired — please log in again.")
        st.rerun()
        return True
    return False

def card(content_fn):
    """Render content inside a dark card via HTML wrapper + st calls."""
    st.markdown('<div class="tc-card">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)

MOOD_EMOJI = {
    "happy": "😊", "sad": "😔", "stressed": "😤",
    "motivated": "💪", "anxious": "😰", "calm": "😌",
    "nostalgic": "🌅", "excited": "🎉", "neutral": "😐",
}

# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "My Capsules"
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "show_landing" not in st.session_state:
    st.session_state["show_landing"] = True

# ─────────────────────────────────────────────
#  LANDING + LOGIN SCREEN
# ─────────────────────────────────────────────
if not st.session_state["access_token"]:
    # Show landing page first for new visitors
    if st.session_state.get("show_landing", True):
        hero_l, hero_mid, hero_r = st.columns([1, 2, 1])
        with hero_mid:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h1 style='color:#fff;font-size:2.2rem;margin-bottom:0.25rem;'>Write to your future self. Let AI help you see how far you've come.</h1>", unsafe_allow_html=True)
            st.markdown("<p style='color:#bbb;font-size:1rem;margin-top:0.25rem;margin-bottom:1.1rem;'>Lock away memories, goals, and photos — then ask an AI companion how your story has unfolded.</p>", unsafe_allow_html=True)
            if st.button("Get Started", key="get_started"):
                st.session_state["show_landing"] = False
                st.rerun()

            # Feature cards
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("<div class='tc-card' style='padding:0.9rem;text-align:center;'><div style='font-size:1.3rem'>📝</div><h4 style='margin:6px 0 4px 0;color:#fff;'>Write letters</h4><p style='color:#bbb;margin:0;font-size:0.9rem;'>Write letters to your future self.</p></div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='tc-card' style='padding:0.9rem;text-align:center;'><div style='font-size:1.3rem'>🤖</div><h4 style='margin:6px 0 4px 0;color:#fff;'>AI Reflection</h4><p style='color:#bbb;margin:0;font-size:0.9rem;'>See your growth over time with AI summaries.</p></div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='tc-card' style='padding:0.9rem;text-align:center;'><div style='font-size:1.3rem'>📷</div><h4 style='margin:6px 0 4px 0;color:#fff;'>Photo memories</h4><p style='color:#bbb;margin:0;font-size:0.9rem;'>Save photos with AI-generated captions.</p></div>", unsafe_allow_html=True)
            with c4:
                st.markdown("<div class='tc-card' style='padding:0.9rem;text-align:center;'><div style='font-size:1.3rem'>📊</div><h4 style='margin:6px 0 4px 0;color:#fff;'>Mood trends</h4><p style='color:#bbb;margin:0;font-size:0.9rem;'>Track your mood over time.</p></div>", unsafe_allow_html=True)

        st.stop()
    # If landing dismissed, show login form with back link
    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("← Back to Intro", key="back_to_intro"):
            st.session_state["show_landing"] = True
            st.rerun()

        st.markdown("## TimeCapsule")
        st.markdown("<p style='color:#888;margin-bottom:1.5rem;'>Your memories, unlocked over time.</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your_username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log in", use_container_width=True)
            if submit:
                resp = safe_request("POST", f"{API_URL}/api/token/", json={"username": username, "password": password})
                if resp:
                    if resp.status_code == 200:
                        st.session_state["access_token"] = resp.json().get("access")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
    st.stop()

# ─────────────────────────────────────────────
#  SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
NAV_PAGES = ["My Capsules", "Write a Capsule", "Reflect", "Search & Mood Trends"]

with st.sidebar:
    st.markdown("<h2 style='color:#fff;font-size:1.2rem;margin-bottom:1.5rem;'>⏳ TimeCapsule</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem;color:#555;margin-bottom:0.75rem;text-transform:uppercase;letter-spacing:0.08em;'>Navigation</p>", unsafe_allow_html=True)

    page_icons = {"My Capsules": "📦", "Write a Capsule": "✍️", "Reflect": "💬", "Search & Mood Trends": "🔍"}
    for page in NAV_PAGES:
        label = f"{page_icons[page]}  {page}"
        if page == st.session_state.get("page"):
            st.markdown(f"<div class='active-nav'>{label}</div>", unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{page}"):
                st.session_state["page"] = page
                st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Notifications in sidebar
    notif_resp = safe_request("GET", f"{API_URL}/api/notifications/", headers=get_headers(), params={"unread_only": "true"})
    if notif_resp and not handle_unauthorized(notif_resp) and notif_resp.status_code == 200:
        unreads = notif_resp.json()
        if unreads:
            st.markdown(f"<span style='color:#f47a6e;font-size:0.85rem;'>🔔 {len(unreads)} new unlock(s)</span>", unsafe_allow_html=True)
            with st.expander("View"):
                for n in unreads:
                    st.caption(n.get("message"))
            if st.button("Mark all as read"):
                for n in unreads:
                    safe_request("PATCH", f"{API_URL}/api/notifications/{n['id']}/", headers=get_headers(), json={"is_read": True})
                st.rerun()

    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
    if st.button("🚪  Log Out"):
        st.session_state["access_token"] = None
        st.session_state["page"] = "My Capsules"
        st.rerun()

# ─────────────────────────────────────────────
#  ACTIVE PAGE INDICATOR IN SIDEBAR
# ─────────────────────────────────────────────
active_page = st.session_state["page"]

# ═════════════════════════════════════════════
#  PAGE: MY CAPSULES
# ═════════════════════════════════════════════
if active_page == "My Capsules":
    st.markdown("## 📦 My Capsules")

    filter_opt = st.radio("", ["All", "Unlocked only", "Locked only"], horizontal=True, label_visibility="collapsed")

    capsules_resp = safe_request("GET", f"{API_URL}/api/capsules/", headers=get_headers(), params={"include_locked": "true"})
    if capsules_resp and not handle_unauthorized(capsules_resp):
        if capsules_resp.status_code == 200:
            capsules = capsules_resp.json()
            if not capsules:
                st.markdown("<div class='tc-card'><p style='color:#666;text-align:center;padding:2rem 0;'>You haven't written any capsules yet — head to <strong>Write a Capsule</strong> to start.</p></div>", unsafe_allow_html=True)
            else:
                capsules.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                for cap in capsules:
                    is_unlocked = cap.get("is_unlocked", False)
                    if filter_opt == "Unlocked only" and not is_unlocked:
                        continue
                    if filter_opt == "Locked only" and is_unlocked:
                        continue

                    mood = cap.get("mood", "")
                    emoji = MOOD_EMOJI.get(mood, "")
                    status_badge = (
                        f"<span class='unlock-badge'>✓ Unlocked</span>"
                        if is_unlocked else
                        f"<span class='lock-badge'>🔒 Locked</span>"
                    )
                    mood_badge = f"<span class='mood-badge'>{emoji} {mood}</span>"

                    st.markdown('<div class="tc-card">', unsafe_allow_html=True)
                    st.markdown(
                        f"<h3 style='margin:0 0 0.25rem 0;font-size:1.05rem;'>{cap.get('title')}{status_badge}{mood_badge}</h3>"
                        f"<p style='color:#555;font-size:0.78rem;margin:0 0 0.75rem 0;'>Created {cap.get('created_at','')[:10]}</p>",
                        unsafe_allow_html=True
                    )

                    if is_unlocked:
                        content = cap.get("content", "")
                        preview = content[:150] + ("..." if len(content) > 150 else "")
                        st.markdown(f"<p style='color:#ccc;font-size:0.9rem;line-height:1.55;'>{preview}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#555;font-size:0.75rem;margin-top:0.5rem;'>Unlocked on {cap.get('unlock_date','')[:10]}</p>", unsafe_allow_html=True)
                    else:
                        unlock_str = cap.get("unlock_date", "")[:10]
                        unlock_dt = datetime.datetime.fromisoformat(cap.get("unlock_date", "").replace("Z", "+00:00"))
                        now_dt = datetime.datetime.now(datetime.timezone.utc)
                        days = (unlock_dt - now_dt).days
                        countdown = f"Unlocks in {days} days" if days > 0 else "Unlocking soon..."
                        st.markdown(f"<p style='color:#f47a6e;font-size:0.9rem;'>🔒 Locked until {unlock_str} &nbsp;·&nbsp; <span style='color:#888;'>{countdown}</span></p>", unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════
#  PAGE: WRITE A CAPSULE
# ═════════════════════════════════════════════
elif active_page == "Write a Capsule":
    st.markdown("## ✍️ Write a Capsule")
    st.markdown("<p style='color:#666;margin-bottom:1.5rem;'>Seal a message to your future self.</p>", unsafe_allow_html=True)

    st.markdown('<div class="tc-card">', unsafe_allow_html=True)
    with st.form("capsule_form"):
        title = st.text_input("Title", placeholder="Give this memory a name...")
        content = st.text_area("Content", placeholder="Write what you want to remember...", height=160)
        col_mood, col_date = st.columns(2)
        with col_mood:
            mood = st.selectbox("Mood", ["happy", "sad", "stressed", "motivated", "anxious", "calm", "nostalgic"])
        with col_date:
            unlock_date = st.date_input("Unlock Date", min_value=datetime.date.today())

        submit_capsule = st.form_submit_button("🔒  Save Capsule", use_container_width=True)
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
                    st.success(f"Capsule sealed! It will unlock on **{unlock_date.isoformat()}**.")
                else:
                    st.error(f"Failed to create capsule: {resp.text}")
    st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════
#  PAGE: REFLECT
# ═════════════════════════════════════════════
elif active_page == "Reflect":
    col_title, col_clear = st.columns([5, 1])
    with col_title:
        st.markdown("## 💬 Reflect")
    with col_clear:
        st.write("")
        if st.button("Clear", help="Clear conversation history (does not delete backend logs)"):
            st.session_state["chat_history"] = []
            st.rerun()

    # Render conversation history
    for turn in st.session_state["chat_history"]:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])
            if turn["role"] == "assistant" and turn.get("referenced_capsules"):
                with st.expander("📎 Capsules referenced"):
                    for cid in turn["referenced_capsules"]:
                        cap_resp = safe_request("GET", f"{API_URL}/api/capsules/{cid}/", headers=get_headers())
                        if cap_resp and cap_resp.status_code == 200:
                            cap_data = cap_resp.json()
                            st.caption(f"**{cap_data.get('title')}** · {cap_data.get('created_at','')[:10]} · mood: {cap_data.get('mood')}")
                        else:
                            st.caption(f"Capsule ID: {cid}")

    # Chat input pinned to bottom
    question = st.chat_input("Ask your past self something...")
    if question:
        st.session_state["chat_history"].append({"role": "user", "content": question, "referenced_capsules": []})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Reflecting on your past entries..."):
                resp = safe_request(
                    "POST",
                    f"{API_URL}/api/capsules/reflect/",
                    headers=get_headers(),
                    json={"question": question}
                )
            if resp and not handle_unauthorized(resp):
                if resp.status_code == 200:
                    data = resp.json()
                    reflection_text = data.get("reflection", "")
                    ref_ids = data.get("referenced_capsules", [])

                    st.write(reflection_text)

                    if ref_ids:
                        with st.expander("📎 Capsules referenced"):
                            for cid in ref_ids:
                                cap_resp = safe_request("GET", f"{API_URL}/api/capsules/{cid}/", headers=get_headers())
                                if cap_resp and cap_resp.status_code == 200:
                                    cap_data = cap_resp.json()
                                    st.caption(f"**{cap_data.get('title')}** · {cap_data.get('created_at','')[:10]} · mood: {cap_data.get('mood')}")
                                else:
                                    st.caption(f"Capsule ID: {cid}")

                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": reflection_text,
                        "referenced_capsules": ref_ids
                    })
                else:
                    st.error(f"Reflection failed: {resp.text}")

# ═════════════════════════════════════════════
#  PAGE: SEARCH & MOOD TRENDS
# ═════════════════════════════════════════════
elif active_page == "Search & Mood Trends":
    st.markdown("## 🔍 Search & Mood Trends")

    # Search
    st.markdown("### Search")
    search_query = st.text_input("", placeholder="Search your unlocked capsules...", label_visibility="collapsed")
    if st.button("Search", key="search_btn"):
        if search_query:
            with st.spinner("Searching your memories..."):
                resp = safe_request("GET", f"{API_URL}/api/capsules/search/", headers=get_headers(), params={"q": search_query})
            if resp and not handle_unauthorized(resp):
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        for r in results:
                            mood = r.get("mood", "")
                            emoji = MOOD_EMOJI.get(mood, "")
                            st.markdown('<div class="tc-card">', unsafe_allow_html=True)
                            st.markdown(
                                f"<h4 style='margin:0 0 0.2rem 0;'>{r.get('title')} <span class='mood-badge'>{emoji} {mood}</span></h4>"
                                f"<p style='color:#555;font-size:0.75rem;margin:0 0 0.6rem 0;'>{r.get('created_at','')[:10]}</p>"
                                f"<p style='color:#ccc;font-size:0.88rem;'>{r.get('content','')[:120]}...</p>",
                                unsafe_allow_html=True
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='tc-card'><p style='color:#666;text-align:center;'>No results found.</p></div>", unsafe_allow_html=True)
                else:
                    st.error(f"Search failed: {resp.text}")

    st.markdown("---")

    # Mood Trends
    st.markdown("### Mood Trends")
    if st.button("Load Trends", key="trends_btn"):
        with st.spinner("Loading your mood history..."):
            resp = safe_request("GET", f"{API_URL}/api/capsules/mood-trends/", headers=get_headers())
        if resp and not handle_unauthorized(resp):
            if resp.status_code == 200:
                trends_data = resp.json()
                if trends_data:
                    df_data = []
                    for month, moods in trends_data.items():
                        for mood_name, count in moods.items():
                            df_data.append({"Month": month, "Mood": mood_name, "Count": count})
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

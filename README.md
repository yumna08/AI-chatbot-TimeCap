# 🕰️ TimeCapsule AI

**Write to your future self. Let AI help you see how far you've come.**

TimeCapsule AI is a full-stack web app for capturing memories, goals, and moments in time-locked "capsules" — then reflecting on them later with an AI companion that grounds every response in your own words.

Unlike a simple journal or scheduled-message app, TimeCapsule AI treats your past entries as a searchable, evolving record. Ask it questions like *"How have I been feeling about my goals lately?"* and it responds by referencing your actual past entries — by date, by mood, by what you really wrote — rather than generating generic advice.

## ✨ Features

- **📝 Time-locked capsules** — Write a letter, note, or memory and set a future unlock date. Content stays completely hidden (enforced at the API level, not just the UI) until that date arrives.
- **🤖 AI Reflection** — A conversational, chat-style interface where an AI companion answers questions about your past using semantic search over your own unlocked entries — never inventing facts, always citing real dates.
- **🔍 Smart Search** — Semantic search across your memories, including natural-language date queries like "my first semester."
- **📷 Photo Capsules** — Attach photos to capsules; Gemini's vision model generates a warm, reflective one-line caption automatically once the capsule unlocks.
- **📊 Mood Trends** — Visualize how your mood has shifted over time, month by month.
- **🔔 Unlock Notifications** — Get notified in-app the moment a capsule becomes unlocked.

## 🛠️ Tech Stack

- **Backend:** Django + Django REST Framework, JWT authentication
- **AI/ML:** Google Gemini (`gemini-2.5-flash` for chat & vision, `gemini-embedding-001` for embeddings) via LangChain
- **Vector Store:** ChromaDB for semantic search and retrieval-grounded reflection
- **Database:** SQLite (dev), Postgres-ready via `dj-database-url`
- **Frontend:** Streamlit — chat-style Reflect interface, capsule timeline, photo uploads, mood analytics

## 🔒 Privacy by Design

Locked capsule content — including text, photos, and AI-generated captions — is never exposed through any API endpoint, regardless of query parameters, until the unlock date has genuinely passed. This is enforced at the serialization layer, not just hidden in the UI.

## 🚀 Getting Started

```bash
# Clone and enter the project
git clone <your-repo-url>
cd TimeCapsule

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your GOOGLE_API_KEY (get one free at https://aistudio.google.com/apikey)

# Run migrations
python manage.py migrate

# Start the backend
python manage.py runserver

# In a separate terminal, start the frontend
streamlit run frontend/app.py
```



Built as a hands-on project to explore LangChain retrieval, prompt engineering for grounded/in-character AI responses, and full-stack development with Django + Streamlit.

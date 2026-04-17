# 🇰🇪 KenyaNews — Automated News Notifier & Website

> AI-powered Kenyan & African news aggregation. Scraped, verified, summarised and published every **10 minutes** — fully automated in the cloud, 100% free.

---

## 🏗️ Architecture

```
GitHub Actions (cron every 10min)
  │
  ├─ scraper/scraper.py      ← RSS feeds (9 sources)
  ├─ scraper/social_scraper.py ← Twitter/X (Nitter), Reddit, Telegram
  ├─ scraper/verifier.py     ← Jaccard similarity + social signals
  ├─ scraper/summarizer.py   ← Hugging Face bart-large-cnn
  ├─ scraper/publisher.py    ← POST to FastAPI backend
  └─ scraper/notifier.py     ← Gmail SMTP digest
       │
  FastAPI backend (Render free tier)
       │
  MongoDB Atlas (free M0 cluster)
       │
  Next.js frontend (Vercel free tier)
```

---

## 📁 Project Structure

```
project/
├── scraper/
│   ├── main.py             # Pipeline orchestrator
│   ├── scraper.py          # RSS + BeautifulSoup
│   ├── social_scraper.py   # Twitter/X, Reddit, Telegram
│   ├── verifier.py         # Multi-source cross-check
│   ├── summarizer.py       # Hugging Face BART
│   ├── publisher.py        # REST publisher
│   ├── notifier.py         # Gmail SMTP email digest
│   └── requirements.txt
├── backend/
│   ├── main.py             # FastAPI app
│   ├── models.py           # Pydantic schemas
│   ├── database.py         # MongoDB via Motor
│   └── requirements.txt
├── frontend/               # Next.js 14 app
│   ├── app/
│   │   ├── page.tsx        # Homepage
│   │   ├── layout.tsx      # Root layout + SEO
│   │   ├── globals.css     # Full design system
│   │   ├── search/         # Search page
│   │   ├── story/[id]/     # Story detail page
│   │   ├── category/[slug]/ # Category page
│   │   ├── sitemap.ts      # Dynamic XML sitemap
│   │   ├── robots.ts       # robots.txt
│   │   └── not-found.tsx   # 404 page
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── StoryCard.tsx
│   │   ├── Ticker.tsx
│   │   ├── Footer.tsx
│   │   └── StatsBar.tsx
│   └── lib/api.ts          # Typed API client
├── .github/workflows/
│   └── scrape.yml          # GitHub Actions pipeline
├── render.yaml             # Render deployment config
├── .env.example            # Environment variable template
└── .gitignore
```

---

## 🚀 Deployment Guide (Step by Step)

### Step 1 — MongoDB Atlas (Database)

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) → **Sign up free**
2. Create a **free M0 cluster** (any region)
3. Create a **database user** with a strong password
4. Under **Network Access** → Add IP `0.0.0.0/0` (allow all)
5. Click **Connect** → **Drivers** → Copy the connection string
6. Replace `<password>` with your database user password
7. Save this as your `MONGODB_URI`

---

### Step 2 — FastAPI Backend on Render

1. Go to [https://render.com](https://render.com) → **Sign up free**
2. **New** → **Web Service** → Connect your GitHub repo
3. Set:
   - **Root directory**: _(leave blank — uses render.yaml)_
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:
   ```
   MONGODB_URI     = <your Atlas URI>
   API_KEY         = <generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
   FRONTEND_URL    = https://your-app.vercel.app
   DB_NAME         = kenyanews
   ```
5. Deploy — note your backend URL (e.g. `https://kenyanews-api.onrender.com`)
6. Test: visit `https://kenyanews-api.onrender.com/health` → should return `{"status":"ok"}`

---

### Step 3 — Frontend on Vercel

1. Go to [https://vercel.com](https://vercel.com) → **Sign up free**
2. **New Project** → Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL   = https://kenyanews-api.onrender.com
   NEXT_PUBLIC_SITE_URL  = https://your-app.vercel.app
   ```
5. Deploy — Vercel will auto-build and host it

---

### Step 4 — GitHub Actions Secrets (Scraper)

In your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret Name              | Value |
|--------------------------|-------|
| `BACKEND_API_URL`        | `https://kenyanews-api.onrender.com` |
| `BACKEND_API_KEY`        | Same as your `API_KEY` on Render |
| `GMAIL_USER`             | `your.email@gmail.com` |
| `GMAIL_APP_PASSWORD`     | Gmail App Password (see below) |
| `NOTIFICATION_RECIPIENTS`| `email1@x.com,email2@x.com` |
| `FRONTEND_URL`           | `https://your-app.vercel.app` |

#### Getting a Gmail App Password:
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. **Security** → **2-Step Verification** (must be enabled)
3. **App passwords** → Select app: **Mail** → Generate
4. Copy the 16-character password → use as `GMAIL_APP_PASSWORD`

---

### Step 5 — Trigger the Pipeline

1. Go to your GitHub repo → **Actions** tab
2. Click **KenyaNews Scraper Pipeline** → **Run workflow**
3. Watch the logs — stories should appear on the website within ~5 minutes
4. The cron job runs automatically every 10 minutes thereafter

---

## 🛠️ Local Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Fill in your MONGODB_URI and API_KEY
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

### Frontend

```bash
cd frontend
npm install
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

### Scraper (test run)

```bash
cd scraper
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Set env vars or create a .env file
python main.py
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/stats` | Total stories, by-category counts |
| `GET` | `/api/stories` | Paginated stories (`?page=1&size=20&category=Kenya`) |
| `GET` | `/api/stories/{id}` | Single story by ID |
| `GET` | `/api/stories/category/{cat}` | Stories by category |
| `GET` | `/api/search?q=...` | Full-text search |
| `POST` | `/api/stories` | Create story (requires `X-API-Key` header) |
| `POST` | `/api/subscribe` | Add email subscriber |

Full interactive docs at `{BACKEND_URL}/docs`

---

## 📰 News Sources

| Source | Category | Type |
|--------|----------|------|
| Standard Media | Kenya | RSS |
| Nation Africa | Kenya | RSS |
| Citizen Digital | Kenya | RSS |
| Kenyans.co.ke | Kenya | RSS |
| Kenya News Agency (KNA) | Kenya | RSS |
| Google News Kenya | Kenya | RSS |
| BBC Africa | Africa | RSS |
| Reuters Africa | Africa | RSS |
| Al Jazeera | World | RSS |
| Twitter/X (via Nitter) | Social | Scrape |
| Reddit (r/Kenya, r/Africa) | Social | JSON API |
| Telegram public channels | Social | Scrape |

---

## ✅ Free Platform Limits

| Platform | Free Limit | Usage |
|----------|-----------|-------|
| GitHub Actions | 2,000 min/month | ~1,440 min/month (10min cron) |
| Render | 750 hrs/month | 1 backend service |
| Vercel | 100GB bandwidth | Frontend |
| MongoDB Atlas | 512MB storage | ~500K stories |
| Hugging Face | Unlimited (CPU) | Model cached between runs |
| Gmail SMTP | 500 emails/day | ~144 digests/day |

---

## 🔒 Security Notes

- Never commit `.env` files — they are in `.gitignore`
- Use a strong randomly generated `API_KEY`
- MongoDB Atlas: restrict network access once deployed
- Gmail: always use App Passwords, never your real password
- Only summaries are published — no full article reproduction

---

## 📦 Tech Stack

- **Scraper**: Python · feedparser · BeautifulSoup · requests
- **AI**: Hugging Face Transformers · facebook/bart-large-cnn
- **Backend**: FastAPI · Motor (async MongoDB) · Pydantic v2
- **Database**: MongoDB Atlas
- **Frontend**: Next.js 14 · TypeScript · Vanilla CSS
- **Automation**: GitHub Actions
- **Hosting**: Vercel (frontend) · Render (backend)
- **Email**: Gmail SMTP

---

*Built with ❤️ for Kenyan journalism. All stories link back to their original sources.*

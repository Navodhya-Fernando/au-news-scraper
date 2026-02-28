# AusMarket Intelligence Feed — Australian News Scraper & Feed

*Real-time news aggregation platform for Australian migration, employment, visa updates, and emerging industries with intelligent filtering and a premium dark UI.*

[![Platform](https://img.shields.io/badge/Platform-Web-4A90E2)](#)
[![Backend](https://img.shields.io/badge/Backend-Python-3776AB)](#)
[![Data Source](https://img.shields.io/badge/Data-GDELT%20API-FF6B6B)](#)
[![UI](https://img.shields.io/badge/UI-Vanilla%20JS-F7DF1E)](#)
[![License](https://img.shields.io/badge/License-MIT-green)](#)

---

## ✨ Overview

**AusMarket Intelligence Feed** is a curated news aggregation system that scrapes, filters, and displays Australia-focused articles about migration, employment, visa pathways, and emerging industries. Built for job and visa consultation businesses, it provides your clients with relevant, up-to-date market intelligence.

---

## 🧠 Core Features

* 🌏 **Smart Scraping** — Fetches from GDELT API (monitoring 100,000+ global sources)
* 🎯 **Intelligent Filtering** — 96%+ filter rate to show only Australia-relevant content
* 🖼️ **Auto Image Fetching** — Extracts article thumbnails with Unsplash fallback
* 📊 **Real-time Progress** — Live progress bar with ETA during scraping
* 🔄 **Incremental Updates** — Only fetches new articles since last update
* 🔍 **Advanced Search** — Filter by keyword, category, source, or date
* 🎨 **Premium Dark UI** — Modern card-based design with smooth animations
* 📱 **Responsive Design** — Works seamlessly on desktop, tablet, and mobile

---

## 📁 Project Structure

```bash
au-news-scraper/
│
├── index.html              # Frontend interface
├── api.py                  # REST API server for scraper
├── assets/
│   ├── css/
│   │   └── styles.css      # Premium dark theme
│   └── js/
│       └── app.js          # Frontend logic
├── scraper/
│   ├── main.py             # Incremental scraper (new articles)
│   ├── main_archive.py     # Full historical scraper
│   └── requirements.txt    # Python dependencies
├── data/
│   ├── articles.json       # Scraped articles database
│   └── meta.json           # Last update timestamp
├── .github/
│   └── workflows/
│       └── deploy.yml      # Auto-deploy to GitHub Pages
├── LICENSE
└── README.md
```

---

## ⚙️ Setup Guide

### 1️⃣ Install Dependencies

```bash
cd scraper
pip install -r requirements.txt
```

### 2️⃣ Run Initial Collection

Collect historical articles (Jan 1, 2026 to present):

```bash
cd scraper
python main_archive.py
```

### 3️⃣ Start the Servers

**Terminal 1 — Web Server:**
```bash
python3 -m http.server 8000
```

**Terminal 2 — API Server:**
```bash
python3 api.py
```

### 4️⃣ Access the App

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 🎯 Query Coverage

The scraper targets 25 query groups across multiple categories:

### 🔐 Visa & Migration (5 queries)
- Australian visa immigration
- Permanent residency pathways (189/190/491)
- Skilled migration programs
- Government immigration policy
- Employer sponsorship programs

### 💼 Employment & Skills (5 queries)
- Australian job market reports
- Skills shortage occupations
- TAFE courses & apprenticeships
- Job interview tips & career advice
- Resume/CV and LinkedIn optimization

### 🏭 Emerging Industries (10 queries)
- IT & Technology
- Logistics & Supply Chain
- Mining & Resources
- Construction & Infrastructure
- Renewable Energy
- Healthcare & Aged Care
- Fintech & Finance
- Agriculture & Farming
- Manufacturing
- Retail & Hospitality

### 📈 Business & Economy (5 queries)
- Australian economy trends
- Business events & conferences
- Government programs
- Market updates
- Training & education

---

## 🔧 API Endpoints

### `POST /api/scrape`
Triggers the scraper to fetch new articles.

**Response:**
```json
{
  "success": true,
  "message": "Scraper started. Poll /api/progress for updates."
}
```

### `GET /api/progress`
Returns real-time scraping progress.

**Response:**
```json
{
  "running": true,
  "current": 15,
  "total": 25,
  "percentage": 60,
  "articles_found": 8,
  "eta_seconds": 45,
  "message": "Searching: 'australia IT technology industry trends'..."
}
```

---

## 🎨 UI Features

* **Search & Filter** — Real-time search across headlines, sources, and categories
* **Sort Options** — Newest first, oldest first, by source, or by category
* **Category Badges** — Color-coded tags for quick identification
* **Image Previews** — Auto-fetched thumbnails with elegant placeholders
* **Progress Bar** — Animated gradient fill with shimmer effect and ETA
* **Responsive Grid** — Auto-adjusting card layout for all screen sizes
* **Dark Theme** — Eye-friendly design optimized for extended reading

---

## 🚀 Deployment

### GitHub Pages (Frontend Only)

1. Push to GitHub
2. Go to **Settings → Pages**
3. Source: **GitHub Actions**
4. The `deploy.yml` workflow will auto-deploy on every push

### Full Stack Deployment

For the scraper button to work on production, you'll need:

1. **Frontend:** GitHub Pages, Netlify, or Vercel
2. **Backend:** Deploy `api.py` on:
   - Heroku
   - Railway
   - DigitalOcean
   - AWS EC2

Update the fetch URL in [assets/js/app.js](assets/js/app.js):
```javascript
const response = await fetch('https://your-api-domain.com/api/scrape', {
    method: 'POST'
});
```

---

## 🧩 Customization

### Add New Query Groups

Edit [scraper/main.py](scraper/main.py):
```python
QUERY_GROUPS = [
    "australia visa immigration",
    "your new query here",
    # ... more queries
]
```

### Change Filtering Rules

Modify the `is_australia_relevant()` function in [scraper/main.py](scraper/main.py) to adjust what articles are included/excluded.

### Update Scraping Frequency

The "Fetch New Articles" button runs incremental updates (only new articles since last run). For automated scraping, add a cron job or scheduled task to run `main.py`.

---

## 📊 Data Flow

```
User clicks "Fetch New Articles"
        ↓
Frontend (app.js) → POST /api/scrape
        ↓
API Server (api.py) → Spawns subprocess
        ↓
Scraper (main.py) → Queries GDELT API
        ↓
Filter → is_australia_relevant() → 96% rejection rate
        ↓
Fetch Images → og:image / twitter:image
        ↓
Save → articles.json + meta.json
        ↓
Frontend polls /api/progress (500ms interval)
        ↓
Display progress bar with ETA
        ↓
Reload articles when complete
```

---

## 🐛 Troubleshooting

**"Failed to connect to scraper API"**
- Make sure `api.py` is running on port 8002
- Check that both servers are running (web on 8000, API on 8002)

**"No new articles found"**
- GDELT may have limited results for niche queries
- Try running `main_archive.py` to collect historical data
- Check that you're not scraping too frequently (wait at least 1 hour between runs)

**Progress bar stuck at 0%**
- The scraper output may be buffered. Restart `api.py`
- Check the API server console for `[SCRAPER]` logs

---

## 📝 Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3.11+ |
| Data Source | GDELT API (primary), Google News RSS (fallback) |
| Parsing | BeautifulSoup4, Requests |
| Storage | JSON files |
| Server | Python http.server, Custom API handler |
| Deployment | GitHub Pages (frontend) |

---

## 🪪 License

MIT License — Copyright © 2026 Navodhya Fernando

See [LICENSE](LICENSE) for full details.

---

## 🤝 Contributing

This is a private client project. For feature requests or issues, contact the developer directly.

---

## 👨‍💻 Developer

**Navodhya Fernando**  
Data & Web System Engineer @DreamShift INC

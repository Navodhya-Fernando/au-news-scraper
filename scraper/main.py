import requests
from bs4 import BeautifulSoup
import json
import os
import base64
from datetime import datetime, timedelta
import time
import random
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Grouped queries focused on migration-related content - AUSTRALIA ONLY
QUERY_GROUPS = [
    "australia visa immigration",
    "australian permanent residency PR pathways",
    "australia skilled migration 189 190 491",
    "australia job market employment",
    "australia skills shortage occupation",
    "australia training courses TAFE apprenticeships",
    "australia emerging industries tech healthcare",
    "australia government immigration policy",
    "australia business events conferences workshops",
    "australian economy employment trends",
    "australia IT technology industry trends",
    "australia logistics supply chain industry",
    "australia mining industry trends",
    "australia construction industry boom",
    "australia renewable energy industry",
    "australia healthcare aged care industry",
    "australia fintech finance industry",
    "australia agriculture farming industry",
    "australia manufacturing industry trends",
    "australia retail hospitality industry",
    "australia employer sponsorship programs",
    "australia job interview tips career advice",
    "australia resume CV writing tips",
    "australia linkedin profile job search",
    "migrants finding jobs australia success"
]

# Unsplash fallback images for categories
CATEGORY_IMAGES = {
    "Australian visa updates": [
        "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&q=80",
        "https://images.unsplash.com/photo-1471922694854-ff1b63b20054?w=800&q=80",
        "https://images.unsplash.com/photo-1526779259212-6d6b1f5d1b4c?w=800&q=80"
    ],
    "PR pathways Australia": [
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&q=80",
        "https://images.unsplash.com/photo-1489515217757-5fd1be406fef?w=800&q=80"
    ],
    "Australian job market reports": [
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80",
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&q=80",
        "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?w=800&q=80"
    ],
    "Emerging industries Australia": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
        "https://images.unsplash.com/photo-1474631245212-32dc3c8310c6?w=800&q=80"
    ],
    "Education & Training": [
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=800&q=80",
        "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=80",
        "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800&q=80"
    ],
    "Government Programs": [
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",
        "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80",
        "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800&q=80"
    ],
    "Market Update": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80"
    ]
}

def pick_fallback_image(category, seed_text):
    images = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["Market Update"])
    if not images:
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80"
    index = abs(hash(seed_text)) % len(images)
    return images[index]

def resolve_google_news_url(url, headers):
    if 'news.google.com' not in url:
        return url
    try:
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if resp.url and 'news.google.com' not in resp.url:
            return resp.url
        soup = BeautifulSoup(resp.text, 'html.parser')
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href') and 'news.google.com' not in canonical['href']:
            return canonical['href']
        og_url = soup.find('meta', property='og:url')
        if og_url and og_url.get('content') and 'news.google.com' not in og_url['content']:
            return og_url['content']
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'news.google.com' not in href:
                return href
    except Exception:
        return url
    return url

def categorize_article(title, description=""):
    text = (title + " " + description).lower()
    if any(word in text for word in ["visa", "migrant", "immigration"]):
        return "Australian visa updates"
    elif any(word in text for word in ["pr", "residence", "citizenship", "pathway"]):
        return "PR pathways Australia"
    elif any(word in text for word in ["job", "employment", "work", "career", "hiring", "labour market", "unemployment"]):
        return "Australian job market reports"
    elif any(word in text for word in ["industry", "sector", "mining", "tech", "business", "economy"]):
        return "Emerging industries Australia"
    elif any(word in text for word in ["course", "training", "skill", "education", "tafe", "apprentice"]):
        return "Education & Training"
    elif any(word in text for word in ["government", "policy", "legislation", "budget", "funding"]):
        return "Government Programs"
    else:
        return None

def is_australia_relevant(title, description=""):
    text = (title + " " + description).lower()
    if "australia" not in text and "australian" not in text:
        return False
    exclude_keywords = [
        "football", "soccer", "cricket", "rugby", "tennis", "afl", "nrl", "nba", "nfl",
        "actor", "actress", "movie", "film", "tv show", "celebrity", "singer", "musician",
        "prince andrew", "royal", "election", "vote", "politician"
    ]
    for keyword in exclude_keywords:
        if keyword in text:
            return False
    visa_keywords = [
        "visa", "migration", "immigration", "skilled worker", "pr pathway", "pr visa",
        "permanent residency", "subclass", "189", "190", "491", "485", "482", "457",
        "citizenship", "skilled migration", "points test"
    ]
    employment_keywords = [
        "employment", "job market", "jobs australia", "hiring", "recruitment",
        "skills shortage", "labour market", "workforce", "unemployment",
        "training", "tafe", "apprentice", "course", "skill development",
        "industry", "economy", "business", "career", "work"
    ]
    has_visa = any(keyword in text for keyword in visa_keywords)
    has_employment = any(keyword in text for keyword in employment_keywords)
    return has_visa or has_employment

def fetch_article_image(url, category, rss_image=None, seed_text=""):
    if rss_image and 'googleusercontent.com' not in rss_image and rss_image.startswith('http'):
        return rss_image
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if img_url.startswith('http') and 'googleusercontent.com' not in img_url:
                return img_url
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            img_url = twitter_image['content']
            if img_url.startswith('http') and 'googleusercontent.com' not in img_url:
                return img_url
        images = soup.find_all('img', src=True)
        for img in images:
            src = img.get('src')
            if src and src.startswith('http'):
                if not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'ad', 'pixel', 'tracking']):
                    return src
    except (requests.Timeout, requests.ConnectionError, Exception):
        pass
    return pick_fallback_image(category, seed_text or url)

def fetch_google_rss_articles(query, start_date, end_date, max_records=20):
    try:
        search_url = f"https://news.google.com/rss/search?q={query}+when:30d&hl=en-AU&gl=AU&ceid=AU:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        return soup.find_all('item', limit=max_records)
    except Exception:
        return []

def fetch_gdelt_articles(keyword, start_date, end_date, max_records=50):
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": keyword,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "sort": "datedesc",
        "startdatetime": start_date.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end_date.strftime("%Y%m%d%H%M%S")
    }
    for attempt in range(3):
        try:
            resp = requests.get(base_url, params=params, timeout=25)
            if resp.status_code in (429, 503):
                time.sleep(2 + attempt)
                continue
            resp.raise_for_status()
            if not resp.text.strip().startswith("{"):
                time.sleep(1 + attempt)
                continue
            data = resp.json()
            return data.get("articles", [])
        except Exception:
            time.sleep(1 + attempt)
            continue
    return []

# --- NEW GITHUB API PUSH FUNCTION ---
def push_to_github(local_file_path, github_file_path, commit_message):
    """Pushes a specific file back to the GitHub repository."""
    print(f"[GITHUB] Pushing {github_file_path}...")
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    if not all([token, owner, repo]):
        print(f"❌ Error: Missing GitHub environment variables. Cannot push {github_file_path}.")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{github_file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_response = requests.get(url, headers=headers)
    sha = get_response.json().get('sha') if get_response.status_code == 200 else None

    with open(local_file_path, "rb") as file:
        content = base64.b64encode(file.read()).decode("utf-8")

    data = {
        "message": commit_message,
        "content": content
    }
    if sha:
        data["sha"] = sha 

    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        print(f"[GITHUB] 🎉 Successfully updated {github_file_path} on GitHub!")
    else:
        print(f"[GITHUB] ❌ Failed to push {github_file_path}: {put_response.json()}")

def scrape_google_news():
    all_articles = []
    new_articles = []
    seen_urls = set()

    end_date = datetime.now()
    meta_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'meta.json')
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'articles.json')

    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if isinstance(existing, list):
                    all_articles.extend(existing)
                    seen_urls.update(a.get('url') for a in existing if a.get('url'))
        except Exception:
            pass
    
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as meta_file:
                meta = json.load(meta_file)
                last_updated = meta.get('last_updated')
                if last_updated:
                    start_date = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S")
                else:
                    start_date = datetime.now() - timedelta(hours=1)
        except Exception:
            start_date = datetime.now() - timedelta(hours=1)
    else:
        start_date = datetime.now() - timedelta(hours=1)

    print(f"\n🔍 INCREMENTAL UPDATE: Collecting new articles from {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}\n")

    for idx, keyword in enumerate(QUERY_GROUPS, 1):
        try:
            print(f"[{idx}/{len(QUERY_GROUPS)}] Searching: '{keyword}'...")
            sys.stdout.flush() 

            matched = 0
            try:
                articles = fetch_gdelt_articles(keyword, start_date, end_date, max_records=60)
            except Exception:
                articles = []

            if articles:
                for article in articles:
                    try:
                        title_text = article.get("title") or ""
                        url = article.get("url") or ""
                        if not title_text or not url or 'news.google.com' in url or url in seen_urls:
                            continue

                        date_str = article.get("seendate")
                        article_date = None
                        if date_str:
                            try:
                                if date_str.endswith('Z'):
                                    article_date = datetime.strptime(date_str, "%Y%m%dT%H%M%SZ")
                                else:
                                    article_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                            except:
                                article_date = datetime.now()
                        else:
                            article_date = datetime.now()

                        if article_date < start_date:
                            continue

                        seen_urls.add(url)
                        snippet = article.get("snippet") or ""
                        category = categorize_article(title_text, snippet)
                        if not category or not is_australia_relevant(title_text, snippet):
                            continue

                        rss_image = article.get("image") or article.get("socialimage")
                        image = fetch_article_image(url, category, rss_image, title_text)
                        source_text = article.get("sourceCommonName") or article.get("domain") or "Global News"

                        new_article = {
                            "headline": title_text,
                            "url": url,
                            "preview_image": image,
                            "source": source_text,
                            "date": article_date.strftime("%Y-%m-%d"),
                            "date_time": article_date.strftime("%Y-%m-%dT%H:%M:%S"),
                            "keyword_category": category
                        }
                        all_articles.append(new_article)
                        new_articles.append(new_article)
                        matched += 1
                        time.sleep(0.05)
                    except Exception:
                        continue
            else:
                items = fetch_google_rss_articles(keyword, start_date, end_date, max_records=20)
                for item in items:
                    try:
                        title_tag = item.find('title')
                        link_tag = item.find('link')
                        pub_date_tag = item.find('pubDate')

                        if not title_tag or not link_tag:
                            continue

                        title_text = title_tag.text.strip()
                        url = link_tag.text.strip()

                        if url in seen_urls:
                            continue

                        article_date = None
                        if pub_date_tag:
                            try:
                                date_str = pub_date_tag.text.strip()
                                article_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                            except:
                                try:
                                    article_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                                except:
                                    article_date = datetime.now()

                        if not article_date:
                            article_date = datetime.now()

                        if article_date < start_date:
                            continue

                        seen_urls.add(url)
                        category = categorize_article(title_text)
                        if not category or not is_australia_relevant(title_text):
                            continue

                        image = fetch_article_image(url, category, seed_text=title_text)
                        source_tag = item.find('source')
                        source_text = source_tag.text.strip() if source_tag else "Google News"

                        new_article = {
                            "headline": title_text,
                            "url": url,
                            "preview_image": image,
                            "source": source_text,
                            "date": article_date.strftime("%Y-%m-%d"),
                            "date_time": article_date.strftime("%Y-%m-%dT%H:%M:%S"),
                            "keyword_category": category
                        }
                        all_articles.append(new_article)
                        new_articles.append(new_article)
                        matched += 1
                        time.sleep(0.1)
                    except Exception:
                        continue

            print(f"  ✅ Found {matched} relevant articles")
            time.sleep(5.0)

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")
            continue

    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    deduped = {}
    for item in all_articles:
        url = item.get('url')
        if not url:
            continue
        deduped[url] = item

    all_articles = list(deduped.values())

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=4, ensure_ascii=False)

    with open(meta_path, 'w', encoding='utf-8') as meta_file:
        json.dump({
            "last_updated": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "range_start": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "range_end": end_date.strftime("%Y-%m-%dT%H:%M:%S")
        }, meta_file, indent=4)

    print(f"\n🎉 Successfully updated! Found {len(new_articles)} NEW articles")
    print(f"📊 Total articles in database: {len(all_articles)}")
    print(f"📊 Unique articles collected: {len(seen_urls)}")

    # --- PUSH TO GITHUB IF NEW ARTICLES EXIST ---
    if len(new_articles) > 0:
        push_to_github(data_path, 'data/articles.json', f"Automated update: Added {len(new_articles)} new articles")
        push_to_github(meta_path, 'data/meta.json', "Automated update: Updated meta.json timestamps")
    else:
        print("[GITHUB] No new articles found. Skipping GitHub push.")

    return len(new_articles)

if __name__ == "__main__":
    scrape_google_news()
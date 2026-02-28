import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import time

# Grouped queries focused on migration-related content for ARCHIVE - AUSTRALIA ONLY
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

# Category images for fallbacks
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
    """Pick a fallback image for a category"""
    images = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["Market Update"])
    if not images:
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80"
    index = abs(hash(seed_text)) % len(images)
    return images[index]

def categorize_article(title, description=""):
    """Categorize article based on keywords"""
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
    """Check if article is relevant to Australia migration/employment topics"""
    text = (title + " " + description).lower()
    
    # Must contain Australia or Australian
    if "australia" not in text and "australian" not in text:
        return False
    
    # Exclude sports, entertainment, politics unrelated to employment
    exclude_keywords = [
        "football", "soccer", "cricket", "rugby", "tennis", "afl", "nrl", "nba", "nfl",
        "actor", "actress", "movie", "film", "tv show", "celebrity", "singer", "musician",
        "prince andrew", "royal", "election", "vote", "politician"
    ]
    
    for keyword in exclude_keywords:
        if keyword in text:
            return False
    
    # Either must have visa/migration keywords OR employment keywords
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
    """Fetch article image with multiple fallback strategies"""
    # If we got an image from RSS, use it directly
    if rss_image and 'googleusercontent.com' not in rss_image and rss_image.startswith('http'):
        return rss_image
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try Open Graph image first (most reliable)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if img_url.startswith('http') and 'googleusercontent.com' not in img_url:
                return img_url
        
        # Try Twitter card image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            img_url = twitter_image['content']
            if img_url.startswith('http') and 'googleusercontent.com' not in img_url:
                return img_url
        
        # Try to find any legitimate article image
        images = soup.find_all('img', src=True)
        for img in images:
            src = img.get('src')
            if src and src.startswith('http'):
                # Skip logos, icons, ads
                if not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'ad', 'pixel', 'tracking']):
                    return src
        
    except (requests.Timeout, requests.ConnectionError, Exception):
        pass
    
    # Use category-specific fallback image
    return pick_fallback_image(category, seed_text or url)

def fetch_gdelt_articles(keyword, start_date, end_date, max_records=50):
    """Fetch articles from GDELT for a keyword and date range"""
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

def scrape_archive_all_articles():
    """Scrape ALL articles from 01/01/2026 to today for archive"""
    all_articles = []
    seen_urls = set()

    end_date = datetime.now()
    start_date = datetime(2026, 1, 1)  # From Jan 1, 2026
    
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'articles.json')
    meta_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'meta.json')

    print(f"\n🔍 ARCHIVE MODE: Collecting ALL articles from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 This will search {len(QUERY_GROUPS)} query groups across {(end_date - start_date).days} days\n")

    total_fetched = 0
    total_relevant = 0
    
    for idx, keyword in enumerate(QUERY_GROUPS, 1):
        try:
            print(f"📰 [{idx}/{len(QUERY_GROUPS)}] Searching: '{keyword}'...", flush=True)

            matched = 0
            fetched = 0

            try:
                articles = fetch_gdelt_articles(keyword, start_date, end_date, max_records=150)
                fetched = len(articles)
                total_fetched += fetched
                print(f"   Retrieved {fetched} articles from GDELT...", flush=True)
            except Exception as e:
                articles = []
                print(f"   ⚠️ GDELT error: {str(e)[:50]}", flush=True)
            except Exception:
                articles = []

            if articles:
                for article in articles:
                    try:
                        title_text = article.get("title") or ""
                        url = article.get("url") or ""
                        if not title_text or not url:
                            continue

                        if 'news.google.com' in url:
                            continue

                        if url in seen_urls:
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

                        # Only include if within date range
                        if article_date < start_date or article_date > end_date:
                            continue

                        seen_urls.add(url)

                        snippet = article.get("snippet") or ""
                        category = categorize_article(title_text, snippet)
                        if not category:
                            continue
                        
                        # Check if article is relevant to Australia migration/employment
                        if not is_australia_relevant(title_text, snippet):
                            continue

                        rss_image = article.get("image") or article.get("socialimage")

                        image = fetch_article_image(url, category, rss_image, title_text)

                        source_text = article.get("sourceCommonName") or article.get("domain") or "Global News"

                        all_articles.append({
                            "headline": title_text,
                            "url": url,
                            "preview_image": image,
                            "source": source_text,
                            "date": article_date.strftime("%Y-%m-%d"),
                            "date_time": article_date.strftime("%Y-%m-%dT%H:%M:%S"),
                            "keyword_category": category
                        })

                        matched += 1
                        total_relevant += 1

                        time.sleep(0.05)

                    except Exception:
                        continue
            
            print(f"  ✅ Found {matched} relevant articles (filtered {fetched - matched} irrelevant)", flush=True)
            time.sleep(2.0)

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}", flush=True)
            continue

    print(f"\n📊 Collection Summary:")
    print(f"   Total articles fetched: {total_fetched}")
    print(f"   Total relevant after filtering: {total_relevant}")
    print(f"   Filtering rate: {((total_fetched - total_relevant) / total_fetched * 100) if total_fetched > 0 else 0:.1f}% filtered out\n")

    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    # De-duplicate by URL and keep the most recent entries
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

    print(f"\n🎉 Successfully saved {len(all_articles)} articles!")
    print(f"📊 Coverage: {len(seen_urls)} unique articles")

    if all_articles:
        dates = [datetime.strptime(a['date'], "%Y-%m-%d") for a in all_articles]
        oldest = min(dates)
        newest = max(dates)
        print(f"📅 Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")

    return len(all_articles)

if __name__ == "__main__":
    scrape_archive_all_articles()

import requests
from bs4 import BeautifulSoup
import json
import os
import urllib.parse
import base64
from datetime import datetime

# Expanded target keywords based on your initial requirements
KEYWORDS = [
    "Australian visa updates",
    "visa for migrants Australia",
    "PR pathways Australia",
    "Australian job market reports",
    "industry stats Australia",
    "emerging industries Australia",
    "government courses training Australia"
]

def fetch_og_image(article_url):
    """Visits the article to grab the preview image."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(article_url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.content, 'lxml')
        og_image = soup.find('meta', property='og:image')
        return og_image['content'] if og_image else "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80"
    except Exception:
        return "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80"

def push_to_github(local_file_path, github_file_path):
    """Pushes the updated JSON file back to the GitHub repository."""
    print("[GITHUB] Preparing to push updated articles.json...")
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    if not all([token, owner, repo]):
        print("❌ Error: Missing GITHUB_TOKEN, GITHUB_OWNER, or GITHUB_REPO environment variables.")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{github_file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get the current file's SHA (required by GitHub to update an existing file)
    get_response = requests.get(url, headers=headers)
    sha = None
    if get_response.status_code == 200:
        sha = get_response.json().get('sha')

    # 2. Read and Base64 encode the new local JSON file
    with open(local_file_path, "rb") as file:
        content = base64.b64encode(file.read()).decode("utf-8")

    # 3. Prepare the payload
    data = {
        "message": f"Automated update: Fetched new articles on {datetime.now().strftime('%Y-%m-%d')}",
        "content": content
    }
    if sha:
        data["sha"] = sha 

    # 4. Make the PUT request to update the file
    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        print("[GITHUB] 🎉 Successfully pushed articles.json to GitHub!")
    else:
        print(f"[GITHUB] ❌ Failed to push: {put_response.json()}")

def scrape_google_news():
    # Define paths
    # Assuming the script runs from the project root (e.g., in Railway)
    data_dir = 'data'
    local_file_path = os.path.join(data_dir, 'articles.json')
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Load existing articles to prevent duplicates
    existing_articles = []
    if os.path.exists(local_file_path):
        try:
            with open(local_file_path, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        except json.JSONDecodeError:
            print("[WARNING] existing articles.json is empty or invalid. Starting fresh.")
            existing_articles = []

    # Create a set of existing URLs for fast O(1) lookups
    existing_urls = {article['url'] for article in existing_articles}
    new_articles = []

    for keyword in KEYWORDS:
        print(f"[SCRAPER] Searching: '{keyword}'...")
        query = urllib.parse.quote(keyword)
        rss_url = f"https://news.google.com/rss/search?q={query}+when:7d&hl=en-AU&gl=AU&ceid=AU:en"

        try:
            response = requests.get(rss_url, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item', limit=3) # Top 3 per keyword

            for item in items:
                google_link = item.link.text
                
                # Check for duplicates before doing the heavy image fetching
                if google_link in existing_urls:
                    continue

                headline = item.title.text
                pub_date = item.pubDate.text
                source_name = item.source.text if item.source else "News Source"

                print(f"  -> Found new: {headline[:40]}...")
                preview_image = fetch_og_image(google_link)

                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                    formatted_date = dt.strftime("%Y-%m-%d")
                except:
                    formatted_date = pub_date 

                new_article = {
                    "headline": headline,
                    "url": google_link,
                    "preview_image": preview_image,
                    "source": f"{source_name} (via Google News)",
                    "date": formatted_date,
                    "keyword_category": keyword
                }
                
                new_articles.append(new_article)
                existing_urls.add(google_link) # Add to set to prevent duplicates within the same run

        except Exception as e:
            print(f"[ERROR] Failed fetching '{keyword}': {e}")

    # Combine new articles with existing ones (putting newest first)
    all_articles = new_articles + existing_articles

    # Save locally in the Railway container
    with open(local_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=4)
        
    print(f"\n[SCRAPER] 🎉 Successfully updated! Found {len(new_articles)} NEW articles")
    print(f"[SCRAPER] 📊 Total articles in database: {len(all_articles)}")

    # Push to GitHub ONLY if we found new articles
    if len(new_articles) > 0:
        # Note: 'data/articles.json' is the path relative to the root of your git repo
        push_to_github(local_file_path=local_file_path, github_file_path='data/articles.json')
    else:
        print("[GITHUB] No new articles found. Skipping GitHub push.")

if __name__ == "__main__":
    scrape_google_news()
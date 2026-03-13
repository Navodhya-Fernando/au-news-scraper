import requests
import json
import os
import urllib.parse
import base64
from datetime import datetime

# GDELT works best with specific phrase matching
KEYWORDS = [
    '"Australian visa"',
    '"PR pathways" Australia',
    '"Australian job market"',
    '"emerging industries" Australia',
    '"government courses" Australia',
    'migrants jobs Australia'
]

def push_to_github(local_file_path, github_file_path):
    """Pushes the updated JSON file back to the GitHub repository."""
    print("[GITHUB] Preparing to push updated articles.json...")
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    if not all([token, owner, repo]):
        print("❌ Error: Missing GitHub environment variables.")
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
        "message": f"GDELT Automated update: Fetched new articles on {datetime.now().strftime('%Y-%m-%d')}",
        "content": content
    }
    if sha:
        data["sha"] = sha 

    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        print("[GITHUB] 🎉 Successfully pushed articles.json to GitHub!")
    else:
        print(f"[GITHUB] ❌ Failed to push: {put_response.json()}")

def scrape_gdelt():
    data_dir = 'data'
    local_file_path = os.path.join(data_dir, 'articles.json')
    os.makedirs(data_dir, exist_ok=True)

    existing_articles = []
    if os.path.exists(local_file_path):
        try:
            with open(local_file_path, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        except json.JSONDecodeError:
            existing_articles = []

    existing_urls = {article['url'] for article in existing_articles}
    new_articles = []

    for keyword in KEYWORDS:
        print(f"[GDELT] Searching: {keyword}...")
        
        # GDELT DOC 2.0 API URL
        # mode=artlist (article list), maxrecords=10 (top 10 per keyword), sort=datedesc (newest first)
        query = urllib.parse.quote(keyword)
        gdelt_url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&maxrecords=10&format=json&sort=datedesc"

        try:
            response = requests.get(gdelt_url, timeout=10)
            
            # GDELT might return empty content if no matches are found for that exact hour
            if not response.text.strip():
                continue
                
            data = response.json()
            articles = data.get('articles', [])

            for item in articles:
                article_url = item.get('url')
                
                if not article_url or article_url in existing_urls:
                    continue

                headline = item.get('title', 'No Title')
                source_name = item.get('domain', 'News Source')
                
                # GDELT natively provides the Open Graph image!
                preview_image = item.get('socialimage', '')
                if not preview_image:
                    preview_image = "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80"

                # GDELT dates look like "20260313T121500Z"
                raw_date = item.get('seendate', '')
                try:
                    dt = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ")
                    formatted_date = dt.strftime("%Y-%m-%d")
                except:
                    formatted_date = datetime.now().strftime("%Y-%m-%d")

                print(f"  -> Found new: {headline[:40]}...")

                new_articles.append({
                    "headline": headline,
                    "url": article_url,
                    "preview_image": preview_image,
                    "source": source_name,
                    "date": formatted_date,
                    "keyword_category": keyword.replace('"', '') # Clean up quotes for the UI badge
                })
                existing_urls.add(article_url)

        except Exception as e:
            print(f"[ERROR] Failed fetching '{keyword}' from GDELT: {e}")

    all_articles = new_articles + existing_articles

    with open(local_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=4)
        
    print(f"\n[GDELT] 🎉 Successfully updated! Found {len(new_articles)} NEW articles")
    print(f"[GDELT] 📊 Total articles in database: {len(all_articles)}")

    if len(new_articles) > 0:
        push_to_github(local_file_path=local_file_path, github_file_path='data/articles.json')
    else:
        print("[GITHUB] No new articles found. Skipping GitHub push.")

if __name__ == "__main__":
    scrape_gdelt()
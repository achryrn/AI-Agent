import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from urllib.parse import urlparse, unquote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

def clean_google_url(url: str) -> str:
    if url.startswith("/url?q="):
        url = url[len("/url?q="):]
        url = url.split("&")[0]
        url = unquote(url)
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") or url.startswith("/search"):
        return ""
    return url

def google_search(query: str, num_results: int = 10) -> List[Dict]:
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        time.sleep(2)  # polite delay
    except Exception as e:
        print(f"[!] Google search request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for g in soup.select('div.g'):
        title_tag = g.select_one('h3')
        link_tag = g.select_one('a')
        snippet_tag = g.select_one('.IsZvec') or g.select_one('.VwiC3b')
        if title_tag and link_tag:
            raw_link = link_tag.get('href', '')
            link = clean_google_url(raw_link)
            if not link:
                continue
            title = title_tag.get_text()
            snippet = snippet_tag.get_text() if snippet_tag else ""
            results.append({"title": title, "link": link, "snippet": snippet})

        if len(results) >= num_results:
            break

    return results

def scrape_page(url: str, max_chars: int = 3000) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return f"Failed to fetch {url}, status: {resp.status_code}"
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try extracting article or main content if present
        main_content = soup.find('article') or soup.find('main') or soup.body
        if main_content:
            paragraphs = main_content.find_all('p')
        else:
            paragraphs = soup.find_all('p')

        text_content = "\n".join(p.get_text() for p in paragraphs)
        return text_content[:max_chars]
    except Exception as e:
        return f"Exception scraping {url}: {str(e)}"

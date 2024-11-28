import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
import re

def extract_urls_from_text(text):
    url_pattern = r'(?:https?://[^\s<>"]+|/[^\s<>"]+)'
    return re.findall(url_pattern, text)

def crawl_site(base_url, max_depth=100):
    visited_links = set()
    links_to_visit = [(base_url, 0)]  # (url, depth)
    urls_from_comments = set()

    while links_to_visit and len(visited_links) < max_depth:
        current_url, depth = links_to_visit.pop(0)
        if current_url in visited_links:
            continue

        try:
            print(f"\nVisiting [{depth}]: {current_url}")
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            visited_links.add(current_url)

            # Check DOCTYPE for URLs
            doctype = response.text.split('\n')[0] if response.text else ""
            if '<!DOCTYPE' in doctype or '<!doctype' in doctype:
                for url in extract_urls_from_text(doctype):
                    full_url = urljoin(base_url, url)
                    urls_from_comments.add((full_url, "DOCTYPE"))

            # Find URLs in comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                for url in extract_urls_from_text(comment):
                    full_url = urljoin(base_url, url)
                    urls_from_comments.add((full_url, comment.strip()))

            # Collect links for further crawling
            if depth < max_depth:
                # Get links from <a> tags and <iframe> tags
                for element in soup.find_all(['a', 'iframe']):
                    href = element.get('href') if element.name == 'a' else element.get('src')
                    if href:
                        full_url = urljoin(base_url, href)
                        parsed_url = urlparse(full_url)
                        
                        if parsed_url.netloc == urlparse(base_url).netloc:
                            if full_url not in visited_links and not any(full_url == url for url, _ in links_to_visit):
                                links_to_visit.append((full_url, depth + 1))

        except requests.exceptions.RequestException as e:
            print(f"Error accessing {current_url}: {e}")

    return urls_from_comments, visited_links

if __name__ == "__main__":
    base_url = "https://softo.ag3nts.org"
    urls_from_comments, visited_links = crawl_site(base_url)
    
    print("\n=== URLs Found in Comments and DOCTYPE ===")
    for url, source in sorted(urls_from_comments):
        print("\n" + "="*50)
        print(f"URL: {url}")
        print(f"Found in: {source[:200]}...")  # Show first 200 chars of source
        print("="*50)

    print("\n=== All Visited Pages ===")
    for url in sorted(visited_links):
        print(url)
    print(f"\nTotal pages visited: {len(visited_links)}")

import requests
from readability import Document
from bs4 import BeautifulSoup  # For stripping HTML tags
from googlenewsdecoder import gnewsdecoder
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

def scrape_save(query):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "DNT": "1",  # Do Not Track
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }

    def extract_article_content(url):
        try:
            newurl = gnewsdecoder(url, interval=10)
            decoded_url = newurl.get("decoded_url")
            if not decoded_url:
                raise ValueError("Decoded URL not found")

            response = requests.get(decoded_url, headers=headers, timeout=10)
            response.raise_for_status()

            doc = Document(response.text)
            summary_html = doc.summary()
            soup = BeautifulSoup(summary_html, "html.parser")
            text_only = soup.get_text(separator="\n", strip=True)

            return text_only

        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return {'error': f'HTTP error: {e.response.status_code}'}
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return {'error': str(e)}

    try:
        logger.info(f"🔍 Searching news for query: {query}")
        search = query
        url = f"https://news.google.com/rss/search?q={search}"

        response = requests.get(url=url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        listnews = soup.find_all('item')[:5]
        if not listnews:
            logger.warning("No news items found.")
            return

        with open("news.txt", "w", encoding="utf-8") as n:
            for i in listnews:
                title = i.find('title').text
                link = i.find('link').text
                content = extract_article_content(link)
                published_on = i.find('pubDate').text
                source = i.find('source').text if i.find('source') else "Unknown"

                item = {
                    "Title": title,
                    "Content": content,
                    "Published_On": published_on,
                    "Source": source
                }
                n.write(str(item) + "\n")

        logger.info("✅ Data written to news.txt")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch news RSS feed: {e}")
    except Exception as e:
        logger.exception(f"❌ Unexpected error in scrape_save: {e}")

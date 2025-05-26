import requests
from readability import Document
from bs4 import BeautifulSoup  # For stripping HTML tags
from googlenewsdecoder import gnewsdecoder

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
            # Step 1: Follow redirect to actual article
            newurl = gnewsdecoder(url, interval=10)
            response = requests.get(url=newurl['decoded_url'], headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Step 4: Extract readable content
            doc = Document(response.text)
            summary_html = doc.summary()

            # Step 5: Clean text
            soup = BeautifulSoup(summary_html, "html.parser")
            text_only = soup.get_text(separator="\n", strip=True)

            return text_only

        except requests.exceptions.HTTPError as e:
            return {'error': f'HTTP error: {e.response.status_code}'}
        except Exception as e:
            return {'error': str(e)}

    search = query
    url = f"https://news.google.com/rss/search?q={search}"

    response = requests.get(url=url,headers=headers)
    soup = BeautifulSoup(response.text, 'xml')
    listnews = soup.find_all('item')[:5]
    impdata = []
    with open("news.txt", "w") as n:
        pass  # This just opens and clears the file

    with open("news.txt", "a" ,encoding="utf-8") as n:
        for i in listnews:
            item = {
                "Title":i.find('title').text, "Content":extract_article_content(i.find('link').text),"Published_On":i.find('pubDate').text, "Source":i.find('source').text
            }
            n.write(str(item))
            n.write('\n')
    print("Data Written To News File")
import requests
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import time
from dotenv import load_dotenv
import os
from post import post
import logging

# Setup
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
model = "GCloud"

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
}

# LLM setup
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    ("system", """You will be given a list of 5 recent news headlines.
    Your task is to:

    Select the most important, relevant, or engaging news item for the general public based on the topic: {topic}.

    Translate the chosen headline into simple, keyword-based layman language suitable for a Google News RSS query.

    Example 1:
    If the headline is:
    "India Surpasses China, Becomes Largest Exporter of iPhones"
    Your output should be:
    india+china+iphone+news

    Example 2 (India-specific):
    If the headline is:
    "PM Modi Launches New National Electric Vehicle Policy to Boost Green Mobility"
    Your output should be:
    pm+modi+electric+vehicle+policy+news

    Example 3 (India-specific):
    If the headline is:
    "Mumbai Records Highest Monsoon Rainfall in a Decade, Authorities on Alert"
    Your output should be:
    mumbai+monsoon+rainfall+alert+news

    Final Output: Just the Google RSS query string (no explanations).

    Only output 1 result."""),  # Truncated for readability
    ("user", "{input}")
])
chain = prompt | llm
topics = ["india","india+politics", "global", "sports", "economic", "entertainment"]

while True:
    for topic in topics:
        try:
            logger.info(f"🔍 Fetching news for topic: {topic}")
            url = f"https://news.google.com/rss/search?q=latest+{topic}+news"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'xml')
            listnews = soup.find_all('item')[:5]
            impdata = [i.find('title').text for i in listnews]

            logger.info(f"Processing headlines: {impdata}")
            result = chain.invoke({"topic": topic, "input": str(impdata)})

            if not result or not result.content:
                logger.warning("LLM returned empty content.")
                continue

            logger.info("Posting English audio...")
            post(result.content, "English", model=model)
            logger.info("English Done")

            time.sleep(10)

            logger.info("Posting Hindi audio...")
            post(result.content, "Hindi", model=model)
            logger.info("Hindi Done")

            logger.info(f"Cycle complete for topic '{topic}': {result.content}")
        except requests.RequestException as e:
            logger.error(f"Network error for topic '{topic}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error for topic '{topic}': {e}")

        logger.info("Sleeping for 1 hour before next news cycle...\n")
        time.sleep(5400)

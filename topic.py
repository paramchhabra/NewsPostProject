from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

def get_query_topic(user_input):
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)


    prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a professional Google News Query Builder.

        The user will provide a news topic or request in plain, everyday language. Your job is to understand the intent and convert it into an accurate, LOWERCASE, short and relevant Google News search query.

        Output Format:
        - Only return the **query string** to be appended after `q=` in this URL: `https://news.google.com/rss/search?q=`
        - Replace spaces with `+` (e.g., `Elon+Musk+Tesla`)
        - Do **not** include the full URL.
        - Do **not** explain or add anything else—just return the query text.

        Goal:
        - Ensure the query covers all key concepts from the user input.
        - Use quotation marks (`%22`) if exact phrases are needed, e.g., `%22climate+change%22`
        - Prefer natural-sounding queries that would return precise news results.

        Examples:
        User: "I want news about the latest iPhone launch"  
        → Query: latest+iPhone+launch
        User: "What's happening with the Ukraine war?"  
        → Query: Ukraine+war+latest
        User: "Any updates on the 2024 Indian elections?"  
        → Query: 2024+Indian+elections+updates
        User: "Give me news about Elon Musk and Tesla"  
        → Query: Elon+Musk+Tesla
        User: "Recent developments in AI regulation"  
        → Query: AI+regulation+recent+developments

        Now, wait for the users request and respond with only the properly formatted Google News query string.
        """)
        ,
        ("user", "{input}")
    ])

    chain = prompt | llm

    response = chain.invoke({
        "input":user_input
    })

    return response.content
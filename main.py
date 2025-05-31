import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from topic import get_query_topic
from scrape import scrape_save
import datetime
from audio import make_audio
from video import generate_fullwidth_waveform_video
from upload import upload
import json

# Load environment variables
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

logo = "LogoS.png"

# LLM setup
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a professional scriptwriter for a YouTube news channel called "FactLine".

        Your job is to generate a {length} Detailed script for a summary video based on news article transcripts on the topic: {topic}. In the language {language}.
        The final script should be suitable for a video lasting approximately {video_time} minutes. Prioritize the information from the articles with the most recent publish date and time.

        You must output your response strictly in the following JSON format:

        {{
        "video_title": "[A concise, catchy, and relevant video title based on the topic and script] | {language}",
        "description": "[A clear and informative video description related to the video content and script]",
        "tags": ["[tag1]", "[tag2]", "[tag3]", "..."],

        "script": "[Your full {language} script goes here]",
        "mood": "[Your mood description goes here, e.g., 'Speak in a Professional and sad tone']"
        }}

        Guidelines:
        - Begin the script with today's date in this format: "It is [todaysdate] and you are watching FactLine." Replace [todaysdate] with {date} in plain {language}.
        - Maintain the tone and factual relevance of the original news transcript(s). Do NOT add any opinions or additional facts.
        - If there are multiple articles or parts, summarize them in logical order, starting from the most recent one.
        - Use simple, engaging, and clear language suitable for a general audience.
        - Attribute facts to the original article if necessary (e.g., "According to [source]...").
        - Do not omit any key information found in the transcript.
        - The video title should be catchy yet professional and directly related to the content.
        - The description should summarize the video content briefly and clearly.
        - Provide 3 to 7 relevant tags that describe the video topic and content.
        - Strictly End the script with a sign-off like: "Thanks for watching FactLine. Stay informed and see you next time." in {language} .

        Important:
        - Your output should follow the JSON structure exactly, and output nothing except for the JSON.
        - Make sure to write the script in a single line
        - The "mood" must always have the word **"Professional"**, e.g., "Speak in a Professional and urgent tone", "Speak in a Professional and hopeful tone", etc.

        Here is the transcript:
        {transcript}
        """),
    ("user", "{input}")
])

chain = prompt | llm

# Streamlit UI
st.title("📰 FactLine - YouTube Script Generator")

user_input = st.text_input("🔍 What news do you want to make a script for?", placeholder="e.g. India Election Results")

length = st.selectbox("📏 Script Length", ["Short", "Long"])
language = st.selectbox("📰 Language", ["English", "Hindi"])
model = st.selectbox("📰 Model", ["GCloud","OpenAI"])



video_time = st.slider("⏱️ Video Time (in minutes)", min_value=5, max_value=20, step=1)
video_time_str = str(video_time)

add_input_choice = st.selectbox("➕ Do you want to add any additional input?", ["No", "Yes"])

additional_input = ""
if add_input_choice == "Yes":
    additional_input = st.text_area("💬 Enter your additional input:")

if st.button("🚀 Submit"):
    if not user_input:
        st.warning("Please enter a news topic.")
    else:
        with st.spinner("⏳ Hold On, Your Video is being uploaded..."):
            topic = get_query_topic(user_input)
            today = datetime.date.today()
            date = today.strftime("%B %d, %Y")

            # Scrape news and get transcript
            scrape_save(topic)
            with open("news.txt", "r", encoding="utf-8") as f:
                transcript = f.read()

            # Generate script from LLM
            response = chain.invoke({
                "length": length,
                "topic": topic,
                "video_time": video_time_str,
                "date": date,
                "transcript": transcript,
                "language": language,
                "input": additional_input
            })

            # Handle JSON response
            content = response.content
            if content.startswith("```"):
                content = content[8:-3]

            data = json.loads(content)

            # Generate audio and video
            audio_name = make_audio(data,language=language,model=model)
            video_name = generate_fullwidth_waveform_video(audio_file=audio_name, logo_file=logo,language=language)

            # Upload the video
            upload(data=data, video_file=video_name,language=language)

        st.success("✅ Video Uploaded Successfully!")



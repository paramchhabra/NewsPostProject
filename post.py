import json
import datetime
import os
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from scrape import scrape_save
from audio import make_audio
from video import create_video, generate_fullwidth_waveform_video
from upload import upload
from image import create_bg_img

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def post(user_input, language, model):
    # Load environment variables
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    logo = "LogoS.png"
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)

    # Prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
            You are a professional scriptwriter for a YouTube news channel called "FactLine".

            Your job is to generate a Short script for a summary video based on news article transcripts on the topic: {topic}, covering Important details to help the listeners understand the news better. 
            In the language {language}.
            The final script should be suitable for a video lasting approximately 60 seconds. Prioritize the information from the articles with the most recent publish date and time.

            You must output your response strictly in the following JSON format:

            {{
            "video_title": "[A very short, catchy, and relevant video title based on the topic and script] | {language} #Shorts",
            "description": "[A clear and informative video description with hashtags related to the video content and script] #Shorts",
            "tags": ["shorts", "[tag2]", "[tag3]", "..."],

            "script": "[Your short {language} script goes here]",
            "mood": "[Your mood description goes here, e.g., 'Speak in a Professional and sad tone']"
            }}

            Guidelines:
            - Begin the script with today's date in this format: "It is [todaysdate] and you are watching FactLine." Replace [todaysdate] with {date} in plain {language}.
            - Maintain the tone and factual relevance of the original news transcript(s). Do NOT add any opinions or additional facts.
            - If there are multiple articles or parts, summarize them in logical order, starting from the most recent one.
            - Use simple, engaging, and clear language suitable for a general audience. Keep sentences concise and avoid unnecessary elaboration to ensure the script fits within a 60-second video.
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
            """),  # (your long prompt here)
        ("user", "")
    ])
    chain = prompt | llm

    today = datetime.date.today()
    date = today.strftime("%B %d, %Y")

    # Scrape and load transcript
    scrape_save(user_input)
    with open("news.txt", "r", encoding="utf-8") as f:
        transcript = f.read()

    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Invoke LLM
            logger.info(f"🔁 Attempt {attempt+1}: Getting response from Groq LLM...")
            response = chain.invoke({
                "topic": user_input,
                "date": date,
                "transcript": transcript,
                "language": language,
            })

            content = response.content.strip()

            # Strip code block markdown
            if content.startswith("```json"):
                content = content[8:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            # Try to parse JSON
            data = json.loads(content)
            logger.info("JSON parsed successfully from LLM response.")
            break

        except json.JSONDecodeError as e:
            logger.warning(f"JSON decoding failed (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error(" All JSON decode attempts failed. Aborting post().")
                return
            continue

        except Exception as e:
            # Check for rate limit error
            if "rate limit" in str(e).lower():
                logger.error("Rate limit error from Groq. Exiting early.")
                return
            logger.error(f"Unexpected error from LLM: {e}")
            return  # Exit on unexpected exception

    # Proceed with media generation
    try:
        audio_name = make_audio(data, language=language, model=model)
        if language == "English":
            create_bg_img(data["video_title"])
        
        if os.path.exists("background.png"):
            video_name = create_video(audio_name,logo,language,"background.png")
        else:
            video_name = generate_fullwidth_waveform_video(audio_name,logo,language=language)
        
        if language == "Hindi":
            os.remove("background.png")
        upload(data=data, video_file=video_name, language=language)
    except Exception as e:
        logger.error(f"Failed during media generation or upload: {e}")

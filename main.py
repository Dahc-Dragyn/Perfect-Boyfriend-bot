import os
import asyncio
import functools
from typing import Callable, List
import requests
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from cachetools import TTLCache
import logging
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import concurrent.futures
from better_profanity import profanity
from persona import PERSONA_PROMPT  # Import the prompt from persona.py

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY is None:
    logger.critical("GEMINI_API_KEY environment variable not set")
    raise EnvironmentError("GEMINI_API_KEY environment variable not set.")

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", "1024"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

# --- Gemini Model Setup ---
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
]

genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel(model_name=MODEL_NAME,
                                 safety_settings=SAFETY_SETTINGS)
except Exception as e:
    logger.error(f"Failed to instantiate Gemini model: {e}")
    raise

# --- Caching & Threading ---
cache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)


async def to_thread(func: Callable, *args, **kwargs):
    loop = asyncio.get_running_loop()
    func_call = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(executor, func_call)

# --- Dad Joke Fetching Function ---


def get_dad_joke():
    url = "https://icanhazdadjoke.com/"
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        joke_data = response.json()
        logger.info("Dad Joke API was called successfully.")
        return joke_data.get(
            'joke',
            "I couldn't fetch a joke right now, but I still think you're awesome!"
        )
    else:
        logger.warning("Failed to fetch joke from Dad Joke API.")
        return "I tried to fetch a joke, but the joke's on me—I couldn't get one!"

# --- Gemini Interaction ---


async def generate_response(user_message: str, session_id: str = None) -> str:
    cache_key = f"{session_id}:{user_message}" if session_id else user_message

    if cache_key in cache:
        logger.debug(f"Cache hit for key: {cache_key}")
        return cache[cache_key]

    try:
        joke_triggers = [
            "joke", "dad joke", "make me laugh", "something funny",
            "need a laugh", "make me chuckle", "be funny", "tell me a joke",
            "got any jokes?"
        ]

        if any(trigger in user_message.lower() for trigger in joke_triggers):
            dad_joke = get_dad_joke()
            personalized_joke = f"Alright, you asked for it! Here's a dad joke fresh off the internet: *{dad_joke}* 😄 Hope that got at least a chuckle!"
            return personalized_joke

        # 1. Retrieve Last Bot Response (if any):
        last_bot_response = cache.get(
            f"{session_id}:last_bot_response")  # From Cache

        messages = [
            {
                "role": "user",
                "parts": [{
                    "text": PERSONA_PROMPT
                }]
            },  # Use imported prompt
        ]

        # 2. Add Last Turn to Messages (if available):
        if last_bot_response:
            messages.append({
                "role": "assistant",
                "parts": [{
                    "text": last_bot_response
                }]
            })

        messages.append({
            "role": "user",
            "parts": [{
                "text": user_message
            }]
        })  # Add new user message

        logger.debug(f"Sending to Gemini: {messages}")

        response = await to_thread(model.generate_content, messages)

        if response.text:
            result = response.text.strip()

            if profanity.contains_profanity(result):
                result = profanity.censor(result)

            cache[cache_key] = result

            # 3. Store the current bot response for the next turn:
            cache[f"{session_id}:last_bot_response"] = result  # Store in Cache

            return result

    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        return "Oops, something went wrong on my end. But hey, I'm still here for you! ❤️"

# --- Data Models, FastAPI Setup, Endpoints ---


class UserMessage(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message.")


class ChatbotResponse(BaseModel):
    response: str = Field(..., description="The chatbot's response.")


app = FastAPI(title="Chatbot API", description="Gemini-powered chatbot")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat", response_model=ChatbotResponse, summary="Chat with the Bot")
async def chat(user_message: UserMessage) -> ChatbotResponse:
    try:
        session_id = "some_session_id"  # Implement session management!
        response_text = await generate_response(user_message.message,
                                               session_id)
        return ChatbotResponse(response=response_text)
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        return ChatbotResponse(
            response=
            "I'm here for romantic and emotional connection. Let's talk about something different."
        )


@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
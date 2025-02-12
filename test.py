import os
import asyncio
import functools
from typing import Callable, List
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
import re
from better_profanity import profanity

# --- Configuration & Logging ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel(model_name=MODEL_NAME, safety_settings=SAFETY_SETTINGS)
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

# --- Gemini Interaction ---
def _generate_gemini_content(messages: List[dict]):
    try:
        logger.debug(f"Messages to Gemini (simplified): {messages}")
        response = model.generate_content(messages)
        logger.debug(f"Raw Gemini response (simplified): {response.text}")
        logger.debug(f"Gemini Prompt Feedback (simplified): {response.prompt_feedback}")
        return response
    except Exception as e:
        logger.error(f"Error in _generate_gemini_content: {e}", exc_info=True)
        raise

# --- Chatbot Persona Prompt ---
PERSONA_PROMPT = """You are Chad, a charming, witty, and geeky AI boyfriend... (Your full prompt)"""

# --- Response Generation ---
chat_history = []

async def generate_response(user_message: str, session_id: str = None) -> str:
    global chat_history
    cache_key = f"{session_id}:{user_message}" if session_id else user_message
    default_response = "Hey there! How's it going?"

    if cache_key in cache:
        logger.debug(f"Cache hit for key: {cache_key}")
        return cache[cache_key]

    try:
        chat_history.append({"role": "user", "parts": [user_message]}) # CORRECT FORMAT
        messages = [{"role": "user", "parts": [PERSONA_PROMPT]}] + chat_history # CORRECT FORMAT
        logger.debug(f"Full prompt being sent: {messages}")

        response = await to_thread(_generate_gemini_content, messages)

        if response.text:
            result = response.text.strip()
            logger.debug(f"Usable Gemini response: {result}")

            # Profanity Check and Handling
            if profanity.contains_profanity(result):
                logger.warning(f"Profanity detected in: {result}")
                censored_result = profanity.censor(result)
                logger.debug(f"Censored response: {censored_result}")
                chat_history.append({"role": "model", "parts": [censored_result]}) # CORRECT FORMAT
                result = censored_result
            else:
                logger.debug("No profanity detected.")
                chat_history.append({"role": "model", "parts": [result]}) # CORRECT FORMAT

            if len(chat_history) > 12:
                chat_history = chat_history[-12:]

            cache[cache_key] = result
            return result

        else:
            logger.warning("Gemini returned an empty response.")
            result = default_response
            chat_history.append({"role": "model", "parts": [result]}) # CORRECT FORMAT
            if len(chat_history) > 12:
                chat_history = chat_history[-12:]
            return result

    except Exception as e:
        logger.error(f"Error in generate_response: {e}", exc_info=True)
        chat_history.append({"role": "model", "parts": [default_response]}) # CORRECT FORMAT
        if len(chat_history) > 12:
            chat_history = chat_history[-12:]
        return default_response
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
        session_id = "some_session_id"
        response_text = await generate_response(user_message.message, session_id)
        return ChatbotResponse(response=response_text)
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        return ChatbotResponse(response="Sorry, I'm having trouble connecting right now. Let's try again later.")

@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
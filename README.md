# Perfect-Boyfriend-bot
Chad The perfect boyfriend
A FastAPI application that integrates with the Gemini model for conversational AI, featuring dad jokes and profanity filtering.

Overview
This project implements a chatbot using the Gemini AI model from Google, enhanced with features like:
Asynchronous handling of requests for better performance.
Integration with external APIs to fetch dad jokes.
Caching mechanism to reduce API calls and improve response times.
Profanity filtering with better_profanity.
Basic session management for maintaining conversation context.

Features
AI Responses: Utilizes the Gemini model for generating responses.
Dad Jokes: Automatically fetches and delivers dad jokes when triggered by specific keywords.
Profanity Filter: Cleans up responses to remove profanity.
API Endpoints: 
/ - Serves a static HTML template for user interaction.
/chat - POST endpoint to interact with the chatbot.
/health - GET endpoint for health checks.

Prerequisites
Before running the application, ensure you have:

Python 3.8+
pip for package management

Installation
Clone the repository:
bash
git clone [your-repo-url]
cd [repo-name]
Install dependencies:
bash
pip install -r requirements.txt
Environment Variables:
Set GEMINI_API_KEY in your environment or .env file.
Optionally configure MODEL_NAME, MAX_WORKERS, CACHE_MAXSIZE, CACHE_TTL.

Example .env file:
GEMINI_API_KEY=your-api-key-here
MODEL_NAME=gemini-1.5-flash
MAX_WORKERS=5
CACHE_MAXSIZE=1024
CACHE_TTL=300

Running the Application
Start the server with:
bash
python main.py
or if using Uvicorn directly:
bash
uvicorn main:app --host 0.0.0.0 --port 8000

API Endpoints
POST /chat: 
Request Body: JSON with message string.
Response: JSON with response string.
GET /: 
Serves the HTML interface for interaction.
GET /health: 
Returns a simple health check status.

Project Structure
main.py: Main application file
persona.py: Contains the persona prompt for the AI (not shown in the code snippet but referenced)
static/: Static files like CSS, JavaScript, images
templates/: HTML templates for rendering

Configuration
Logging: Configured to log at INFO level by default.
Safety Settings: Gemini model uses specified safety thresholds.

Notes
Threading: Uses ThreadPoolExecutor for managing concurrent operations.
Caching: TTLCache for caching responses to reduce API load and speed up response times.
Profanity: Uses better_profanity for censoring responses.

Future Improvements
Implement true session management for better context retention across multiple requests.
Enhance error handling and logging for production use.
Add more triggers or a more sophisticated method for engaging dad joke feature.
Performance tuning based on usage patterns.

# AI-Powered Finance Interview System

An end-to-end AI-powered interview system designed for finance firms to automate their interview process. The system uses OpenAI's API to generate relevant questions, evaluate responses, and provide comprehensive scoring.

## Features

- Dynamic interview question generation
- Real-time response evaluation
- Comprehensive scoring system
- Candidate progress tracking
- Technical and behavioral assessment capabilities

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `POST /interview/start`: Start a new interview session
- `POST /interview/question`: Get the next question
- `POST /interview/answer`: Submit and evaluate an answer
- `GET /interview/score`: Get the current interview score
- `GET /interview/summary`: Get a summary of the interview

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: Database connection string (optional) 
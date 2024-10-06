

# AI-Powered Resume Summarizer

This project is a web application that allows users to upload resumes (in PDF format), extracts key details like skills, experience, and education, generates a summary, and creates personalized interview questions using OpenAI's GPT model.

## Features:
- Upload your resume (PDF)
- Extracts key sections like Skills, Experience, Education, and Projects
- Generates a concise resume summary
- Generates interview questions based on the extracted details

---

## Prerequisites:
- Python 3.7+
- Node.js and npm (for the React frontend)
- [OpenAI API Key](https://beta.openai.com/signup/)

---

## Installation and Setup

### 1. Backend (Python/Django)
1. Clone this repository.
2. Navigate to the backend folder.
   
   ```bash
   cd resume_summarizer_backend
   ```
3. Create and activate a virtual environment:
   
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

4. Install the required dependencies:
   
   ```bash
   pip install -r requirements.txt
   ```

5. Add your OpenAI API key by editing the `openai_integration.py` file:
   
   ```python
   openai.api_key = 'ADD-YOUR-OPEN-AI-API-KEY-HERE'
   ```

6. Run the Django development server:

   ```bash
   python manage.py runserver
   ```

---

### 2. Frontend (React)
1. Navigate to the frontend folder:
   
   ```bash
   cd resume_summarizer_frontend
   ```

2. Install the required dependencies:
   
   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm start
   ```



## Environment Variables

Make sure you have the following environment variables set up:

- **For OpenAI API Key:**
  
  In `project\resume_summarizer_backend\gpt_integration\openai_integration.py`, replace the placeholder with your actual OpenAI API key:

  ```python
  openai.api_key = 'ADD-YOUR-OPEN-AI-API-KEY-HERE'
  ```

---

## Usage

1. Navigate to `http://localhost:3000` in your browser.
2. Upload your resume in PDF format.
3. View the extracted resume summary and generated interview questions.
4. Toggle between light and dark mode to see dynamic background changes.
5. The Uploaded Resumes are saved in `project\resume_summarizer_backend\resumes`.
6. The JSON files are saved in `project\resume_summarizer_backend\saved_jsons`.


---

## Project Structure

```
backend/               # Django project for backend (resume processing, OpenAI integration)
frontend/              # React project for frontend
saved_jsons/           # Directory for saving processed resume JSON files
public/                # Directory for public assets (background images)
README.md              # This file
```

---






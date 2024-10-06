
import openai
import json
import os

# Set your OpenAI API key
openai.api_key = 'ADD-YOUR-OPEN-AI-API-KEY-HERE'

def clean_text(text):

    return text.replace("**", "").strip()

def generate_resume_summary_and_questions(extracted_text, file_name):


    
    if not file_name.endswith('.json'):
        file_name = f"{file_name}.json"

    
    prompt = f"""
    Here is a resume text:
    {extracted_text}

    1. Extract the following sections from the resume:
       - Skills
       - Education
       - Projects
       - Experience

    2. Summarize the resume in 3-4 sentences.

    3. Generate 5 interview questions based on the extracted skills, projects, and experience.
    """

    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        n=1,
        temperature=0.7
    )

    
    output_text = response['choices'][0]['message']['content'].strip()

    
    skills_start = output_text.find("Skills:")
    education_start = output_text.find("Education:")
    projects_start = output_text.find("Projects:")
    experience_start = output_text.find("Experience:")
    summary_start = output_text.find("Summary:")
    questions_start = output_text.find("Interview Questions:")

    
    skills = clean_text(output_text[skills_start:education_start].replace("Skills:", "").strip()) if skills_start != -1 else ""
    education = clean_text(output_text[education_start:projects_start].replace("Education:", "").strip()) if education_start != -1 else ""
    projects = clean_text(output_text[projects_start:experience_start].replace("Projects:", "").strip()) if projects_start != -1 else ""
    experience = clean_text(output_text[experience_start:summary_start].replace("Experience:", "").strip()) if experience_start != -1 else ""
    summary = clean_text(output_text[summary_start:questions_start].replace("Summary:", "").strip()) if summary_start != -1 else ""

    
    questions_text = output_text[questions_start:].replace("Interview Questions:", "").strip() if questions_start != -1 else ""
    questions_list = [clean_text(q.strip()) for q in questions_text.split('\n') if q.strip()]
    
    
    questions = []
    for i, q in enumerate(questions_list, start=1):
        if len(q) > 2:  
            if q[0].isdigit() and q[1] == '.':
                q = q[q.find('.') + 1:].strip()
            questions.append(f"{i}. {q}")

    
    output_data = {
        "extracted_sections": {
            "skills": skills,
            "education": education,
            "projects": projects,
            "experience": experience
        },
        "summary": summary,
        "questions": questions,
        "user_answers": {
            "answers_to_questions": ["" for _ in questions]  
        }
    }

    
    json_file_path = os.path.join('saved_jsons', file_name)

    
    count = 1
    base_file_name = file_name.rsplit('.json', 1)[0]
    while os.path.exists(json_file_path):
        json_file_path = os.path.join('saved_jsons', f"{base_file_name}_{count}.json")
        count += 1

    
    with open(json_file_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    
    return output_data

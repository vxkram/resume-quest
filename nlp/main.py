
import os
import json

from nlp.resume_processor import extract_text_from_pdf
from nlp.extract_skills import load_skills_from_csv, extract_skills
from nlp.extract_education import extract_education
from nlp.extract_experience import extract_experience
from nlp.summary import generate_summary
from nlp.questions import generate_questions
from nlp.extract_projects import extract_projects


if __name__ == '__main__':
  
    csv_path = 'D:/resume_project/csv_files/skills.csv'
    skills_db = load_skills_from_csv(csv_path)

 
    pdf_path = 'D:/resume_project/resume/Vikram.pdf'
    

    name = os.path.basename(pdf_path).replace(".pdf", "").replace("_", " ")

 
    resume_text = extract_text_from_pdf(pdf_path)

   
    skills = extract_skills(resume_text, skills_db)
    education_info = extract_education(resume_text)
    experience_info = extract_experience(resume_text)
    projects = extract_projects(resume_text)


    summary = generate_summary(name, skills, education_info, experience_info)
    print("\nGenerated Summary:\n", summary)


    interview_questions = generate_questions(skills, projects, experience_info)


    data = {
        "name": name,
        "summary": summary,
        "questions": [
            {
                "question_number": i + 1,
                "question_text": question,
                "answer": ""  
            }
            for i, question in enumerate(interview_questions)
        ]
    }


    json_file_path = 'D:/resume_project/output/resume_summary_and_questions.json'

   
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print("\nSummary and Interview Questions have been saved to:", json_file_path)



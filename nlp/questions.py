import random

def generate_questions(skills, projects, experience):

    questions = []


    skills = list(skills)


    if skills:
        for skill in skills[:3]: 
            questions.append(f"Can you explain your experience working with {skill}?")
            questions.append(f"What challenges did you face when using {skill}?")
            questions.append(f"How would you improve your workflow with {skill}?")

  
    if projects:
        for project in projects[:2]: 
            questions.append(f"Can you describe your role in the {project} project?")
            questions.append(f"What challenges did you encounter while working on {project}?")

    if experience:
        for exp in experience[:2]:  
            questions.append(f"Can you describe your responsibilities at {exp}?")
            questions.append(f"What challenges did you face while working at {exp}?")
            questions.append(f"How did you contribute to the success of the team at {exp}?")


    return random.sample(questions, min(6, len(questions)))

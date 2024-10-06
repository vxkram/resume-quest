def generate_summary(name, skills, education, experience):


    if skills:
        skills_text = ', '.join(skills)
        skills_summary = f"{name} has expertise in the following technical skills: {skills_text}."
    else:
        skills_summary = f"{name} has technical skills, but they are not clearly defined."


    if education:
        education_summary = f"{name} holds a {education[0]}."
    else:
        education_summary = f"{name}'s educational background is not available."

    if experience:
        experience_summary = f"{name} has worked with organizations such as: " + ' '.join(experience[:3]) + "."
    else:
        experience_summary = f"{name}'s professional experience is not available."

    summary = f"{skills_summary} {education_summary} {experience_summary}"

    return summary

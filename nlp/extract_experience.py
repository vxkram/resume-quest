import re

def extract_experience(input_text):

 
    experience_pattern = r'(experience[:\s]+)(.*?)(education|skills|projects|$)'
    experience_match = re.search(experience_pattern, input_text, re.IGNORECASE | re.DOTALL)

    if not experience_match:
        return "No experience information found."


    experience_section = experience_match.group(2).strip()


    experience_lines = experience_section.split('\n')
    experience_details = [line.strip() for line in experience_lines if line.strip()]

    return experience_details if experience_details else "No detailed experience information found."



import re

def extract_education(input_text):

    # Look for the "Education" section and extract everything following it
    education_pattern = r'(education[:\s]+)(.*?)(experience|skills|projects|work|internship|achievements|languages|$)'
    education_match = re.search(education_pattern, input_text, re.IGNORECASE | re.DOTALL)

    if not education_match:
        return "No education information found."

    # Extracted education section
    education_section = education_match.group(2).strip()

    # Define a pattern for degrees and institutions
    degree_pattern = r'(Bachelor|Master|Ph\.D|B\.E|B\.Tech|M\.Tech|BSc|MSc|BBA|MBA)\s*(of\s*\w+)?'
    institution_pattern = r'(college|university|academy|institute|school)'

    # Extract degrees and institutions using regex
    degrees = re.findall(degree_pattern, education_section, re.IGNORECASE)
    institutions = re.findall(institution_pattern, education_section, re.IGNORECASE)

    # Combine degrees and institutions
    extracted_education = []
    for degree in degrees:
        extracted_education.append(f"{degree[0]} {degree[1].strip() if degree[1] else ''}".strip())

    # Return degrees with institutions (simple matching)
    if extracted_education:
        return extracted_education
    return "No education details found."



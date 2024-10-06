import re

def extract_projects(input_text):

    project_pattern = r"(Projects|Relevant Projects|Project Work):([\s\S]+?)(?=\n\n|\Z)"
    match = re.search(project_pattern, input_text, re.IGNORECASE)
    
    if match:
        project_section = match.group(2)
        

        project_lines = project_section.split('\n')
        

        project_names = [line.strip() for line in project_lines if re.match(r'^[A-Z].+', line)]
        
        return project_names if project_names else "No project names found"
    
    return "Projects section not found"

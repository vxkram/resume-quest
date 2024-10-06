import pandas as pd
import nltk
import os
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker_tab')


def download_nltk_resources():
    """
    Downloads necessary NLTK resources if not present
    """
    nltk_resources = [
        'punkt', 'maxent_ne_chunker', 'words', 'stopwords'
    ]
    
    for resource in nltk_resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource)


download_nltk_resources()



def load_skills_from_csv(csv_path):

    df = pd.read_csv(csv_path)
    skills_list = df.iloc[:, 0].tolist()  
    return [skill.lower() for skill in skills_list]

def extract_skills(input_text, skills_db):

    stop_words = set(nltk.corpus.stopwords.words('english'))
    word_tokens = nltk.tokenize.word_tokenize(input_text)


    filtered_tokens = [w for w in word_tokens if w.lower() not in stop_words]

  
    filtered_tokens = [w for w in filtered_tokens if w.isalpha()]


    bigrams_trigrams = list(map(' '.join, nltk.everygrams(filtered_tokens, 2, 3)))

  
    found_skills = set()


    for token in filtered_tokens:
        if token.lower() in skills_db:
            found_skills.add(token)

 
    for ngram in bigrams_trigrams:
        if ngram.lower() in skills_db:
            found_skills.add(ngram)

    return found_skills



RESERVED_DEGREES = [
    'bachelor', 'master', 'phd', 'high school', 'doctorate'
]

RESERVED_WORDS = [
    'school', 'college', 'university', 'academy', 'institute', 'faculty'
]

def extract_education(input_text):
    """
    Extracts both educational institutions and degrees from the resume text using NLTK.
    The function looks for organizations (using NER) and degree-related terms like "Bachelor" and "Master".
    """
    organizations = []
    degrees = []

    # Extract organizations (e.g., educational institutions) using NLTK's named entity recognition
    for sent in nltk.sent_tokenize(input_text):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
            if hasattr(chunk, 'label') and chunk.label() == 'ORGANIZATION':
                organizations.append(' '.join(c[0] for c in chunk.leaves()))

    # Search for educational institutions in the organizations list
    education_institutions = set()
    for org in organizations:
        for word in RESERVED_WORDS:
            if word.lower() in org.lower():
                education_institutions.add(org)

    # Search for degrees in the text (bachelor, master, phd, etc.)
    for sent in nltk.sent_tokenize(input_text):
        for word in nltk.word_tokenize(sent):
            if word.lower() in RESERVED_DEGREES:
                degrees.append(word.capitalize())

    # Combine the degree with the institution name
    extracted_education = []
    for degree in degrees:
        for institution in education_institutions:
            extracted_education.append(f"{degree} from {institution}")

    return extracted_education if extracted_education else "No education information found."






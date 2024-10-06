import pandas as pd
import nltk

nltk.download('stopwords')

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

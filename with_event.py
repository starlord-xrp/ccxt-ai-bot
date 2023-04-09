import requests
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm

# Load spaCy model
nlp = en_core_web_sm.load()

# Function to get news articles from Bing News Search API
def get_news(query):
    url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"
    payload = {"q": query}
    headers = {
        "Ocp-Apim-Subscription-Key": "YOUR_API_KEY_HERE",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    }
    response = requests.get(url, params=payload, headers=headers)
    articles = response.json()["value"]
    return articles

# Function to extract named entities from news articles
def extract_entities(articles):
    entities = []
    for article in articles:
        doc = nlp(article["description"])
        for ent in doc.ents:
            if ent.label_ in ["ORG", "GPE", "LOC", "EVENT"]:
                entities.append(ent.text)
    return entities

# Function to identify major events based on named entities
def identify_events(entities):
    events = []
    for entity, count in Counter(entities).most_common():
        if count >= 3: # threshold for identifying major events
            events.append(entity)
    return events

# Example usage
articles = get_news("XRP")
entities = extract_entities(articles)
events = identify_events(entities)
print(events)

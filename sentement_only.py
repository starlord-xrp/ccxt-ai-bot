import requests
import json
import time

# API keys and endpoints
BING_NEWS_API_KEY = 'your_bing_news_api_key'
SENTIMENT_140_API_KEY = 'your_sentiment_140_api_key'
BING_NEWS_ENDPOINT = 'https://api.cognitive.microsoft.com/bing/v7.0/news/search'
SENTIMENT_140_ENDPOINT = 'https://api.sentiment140.com/v1/analyze'

# Query parameters for Bing News API
params = {
    'q': 'XRP', # search query
    'count': 100, # number of news articles to fetch
    'freshness': 'Day', # articles from last 24 hours
    'mkt': 'en-US' # market
}

# Function to get sentiment of text using Sentiment140 API
def get_sentiment(text):
    data = {'text': text, 'api_key': SENTIMENT_140_API_KEY}
    response = requests.post(SENTIMENT_140_ENDPOINT, data=data)
    result = json.loads(response.text)
    sentiment = result['results']['polarity']
    return sentiment

# Function to get average sentiment of news over last 24 hours
def get_average_sentiment():
    # Get news from Bing News API
    headers = {'Ocp-Apim-Subscription-Key': BING_NEWS_API_KEY}
    response = requests.get(BING_NEWS_ENDPOINT, headers=headers, params=params)
    news = json.loads(response.text)
    
    # Calculate average sentiment of news
    total_sentiment = 0
    article_count = 0
    for article in news['value']:
        sentiment = get_sentiment(article['description'])
        total_sentiment += sentiment
        article_count += 1
    
    if article_count == 0:
        return None
    
    average_sentiment = total_sentiment / article_count
    
    return average_sentiment

# Loop to continuously get sentiment every 15 minutes
while True:
    sentiment = get_average_sentiment()
    if sentiment is not None:
        print(f"Average sentiment over last 24 hours: {sentiment}")
    else:
        print("No news found")
    time.sleep(900) # 15 minutes in seconds

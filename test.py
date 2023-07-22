import requests
from bs4 import BeautifulSoup
import openai
import json


def crawl_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    content = []
    for article in soup.find_all("article"):
        content.append(article.text)
    return content


def train_chatgpt_model(content):
    openai.api_key = "YOUR_API_KEY"
    training_data = []
    for text in content:
        training_data.append({
            "prompt": text,
            "completion": text
        })
    training_data.append({
        "prompt": "Hi, how may I help you today?",
        "completion": "I need help with my account. I can't seem to log in."
    })
    training_data.append({
        "prompt": "What is this website about?",
        "completion": "This website is about cats. It provides information on a wide range of topics, including cat breeds, cat care, and cat behavior. The website also includes a forum where cat owners can discuss their cats and share tips."
    })
    training_data.append({
        "prompt": "I'm looking for a specific product. Can you help me find it?",
        "completion": "Sure, I can help you with that. What product are you looking for?"
    })
    training_data.append({
        "prompt": "I'm having trouble with my order. Can you help me?",
        "completion": "Sure, I can help you with that. What seems to be the problem with your order?"
    })
    training_data.append({
        "prompt": "I'm not sure if this is the right website for me. Can you help me?",
        "completion": "Sure, I can help you with that. What are you looking for in a website?"
    })
    openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-0613",
        training_data = json.dumps(training_data),
    )


def customer_service_chat(prompt):
    openai.api_key = "YOUR_API_KEY"
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-0613",
    messages = [{
        "role": "user",
        "content": prompt
    }],
    )
    return response["choices"][0]["message"]


if __name__ == "__main__":
    url = "https://www.example.com"
content = crawl_website(url)
train_chatgpt_model(content)
prompt = "What is this website about?"
response = customer_service_chat(prompt)
print(response)
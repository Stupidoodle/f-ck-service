from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import openai
import json
import urllib.parse

all_content = []
all_images = []
all_videos = []
all_links = []
visited_links = []

def crawl_website(url):
    if url in visited_links:
        return

    response = requests.get(url)
    visited_links.append(url)

    soup = BeautifulSoup(response.content, "html.parser")
    content = []
    images = []
    videos = []
    links = []
    for article in soup.find_all("article"):
        content.append(article.text)
        image = article.find("img")
        if image:
            images.append(image["src"])
            image_tag = f'<img src="{image["src"]}" alt="{image["alt"]}" />'
            content.append(image_tag)
        video = article.find("video")
        if video:
            videos.append(video["src"])
        link = article.find("a")
        if link:
            links.append(link["href"])
    return [content, images, videos, links]


def crawl_website_recursively(url):
    if url in visited_links:
        return

    crawled_site = crawl_website(url)
    all_content.append(crawled_site[0])
    all_links = crawled_site[3]

    for link in all_links:
        if link not in visited_links and get_domain(link) == get_domain(url):
            visited_links.append(link)
            crawl_website_recursively(link)



def get_domain(url):
    domain = urllib.parse(url).netloc
    return domain

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prompt = request.form["prompt"]
        response = customer_service_chat(prompt)
        return render_template("index.html", prompt=prompt, response=response)
    return render_template("index.html", prompt="", response="")


if __name__ == "__main__":
    url = "https://www.example.com"
    crawled_site = crawl_website(url)
    content = crawled_site[0]
    all_links = crawled_site[1]
    train_chatgpt_model(all_content)
    app.run(debug=True)

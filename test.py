from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import openai
import json
from urllib.parse import urljoin
import urllib.parse
import credentials

app = Flask(__name__)

content = []
all_images = []
all_videos = []
all_links = []
visited_links = []

def get_sublinks(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    sublinks = set()

    for link in soup.find_all("a"):
        href = link.get("href")
        if href and not href.startswith("#"):
            sublink = urljoin(url, href)
            sublinks.add(sublink)

    return sublinks

# ... (previous code)

def crawl_website(url):
    print("Visiting: " + url)
    response = requests.get(url)
    visited_links.append(url)

    soup = BeautifulSoup(response.content, "html.parser")
    if len(soup.getText()) >= 100:
        print("Found Content on Site. Appending...")
        content.append(soup.getText())  # Append to the global content list

    images = []
    videos = []
    links = []
    sublinks = get_sublinks(url)
    all_links.extend(sublinks)

    for link in sublinks:
        if link not in visited_links and get_domain(link) == get_domain(url):
            visited_links.append(link)
            # Use a local content list for each recursive call
            crawl_website(link)

    return content


# ... (rest of the code)


def get_domain(url):
    domain = urllib.parse.urlparse(url).netloc
    return domain

def train_chatgpt_model(content):
    openai.api_key = credentials.api_key
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
    openai.api_key = credentials.api_key
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-0613",
    messages = [{
        "role": "user",
        "content": prompt
    }],
    )
    print(response["choices"][0]["message"]["content"])
    return response["choices"][0]["message"]["content"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        prompt = data.get("prompt", "")
        response = customer_service_chat(prompt)
        return jsonify({"response": response})
    return render_template("index.html", prompt="", response="")

if __name__ == "__main__":
    url = "https://www.vapiano.de/de/"
    #crawl_website(url)
    #with open("output.txt", "w", encoding="utf-8") as txt_file:
        #for item in content:
            #txt_file.write(item + "\n")

    #webhooktest
    #train_chatgpt_model(content)
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import openai
import json
from urllib.parse import urljoin
import urllib.parse
import credentials
import PyPDF2
import io
from summa.summarizer import summarize  # Import the text summarization library
import tiktoken
from transformers import pipeline

app = Flask(__name__)

content = []
all_images = []
all_videos = []
all_links = []
visited_links = []

app = Flask(__name__)

content = []
all_images = []
all_videos = []
all_links = []
visited_links = []

import gensim

def summarize_with_tokens(text, remaining_tokens):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summary = summarizer(text, max_length=512, min_length=50, do_sample=False)[0]['summary_text']
    tokens_in_summary = num_tokens_from_messages([{"role": "user", "content": summary}], model="gpt-3.5-turbo-16k")
    remaining_tokens -= tokens_in_summary
    return summary, remaining_tokens


def download_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        print("Error while downloading PDF:", str(e))
        return None

def convert_pdf_to_text(pdf_content):
    try:
        if pdf_content is None:
            return None

        pdf_file = io.BytesIO(pdf_content)
        pdfreader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdfreader.pages)
        text = ""

        for page_num in range(num_pages):
            pageobj = pdfreader.pages[page_num]
            text += pageobj.extract_text()

        return text

    except Exception as e:
        print("Error while converting PDF to text:", str(e))
        return None

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

visited_pdfs = []

def crawl_website(url, remaining_tokens):
    print("Visiting: " + url)
    response = requests.get(url)
    visited_links.append(url)

    soup = BeautifulSoup(response.content, "html.parser")

    if len(soup.getText()) >= 100:
        print("Found Content on Site. Appending...")
        summary, remaining_tokens = summarize_with_tokens(soup.getText(), remaining_tokens)
        content.append(summary)  # Append to the global content list

    sublinks = get_sublinks(url)
    all_links.extend(sublinks)

    for link in sublinks:
        # Check if the link points to an image or video
        if link.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            print("Found Image. Skipping...: " + link)
            all_images.append(link)
            visited_links.append(link)
            continue
        
        if link.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            print("Found Video. Skipping...: " + link)
            all_videos.append(link)
            visited_links.append(link)
            continue

        if link.lower().endswith('.pdf'):
            if link not in visited_pdfs:
                print("Found PDF. Converting to plain text...: " + link)
                pdf_content = download_pdf(link)
                pdf_text = convert_pdf_to_text(pdf_content)
                print(pdf_text)
                content.append(pdf_text)
                visited_pdfs.append(link)

        if link not in visited_links and get_domain(link) == get_domain(url):
            visited_links.append(link)
            crawl_website(link, remaining_tokens)

    return content

def get_domain(url):
    domain = urllib.parse.urlparse(url).netloc
    return domain

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-16k"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-16k":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")

def train_chatgpt_model(content):
    openai.api_key = credentials.api_key
    example_prompts = [
        ("Hi, how may I help you today?", "I need help with my account. I can't seem to log in."),
        ("What is this website about?", "This website is about cats. It provides information on a wide range of topics, including cat breeds, cat care, and cat behavior. The website also includes a forum where cat owners can discuss their cats and share tips."),
        ("I'm looking for a specific product. Can you help me find it?", "Sure, I can help you with that. What product are you looking for?"),
        ("I'm having trouble with my order. Can you help me?", "Sure, I can help you with that. What seems to be the problem with your order?"),
        ("I'm not sure if this is the right website for me. Can you help me?", "Sure, I can help you with that. What are you looking for in a website?")
    ]

    # Calculate the maximum number of tokens allowed per API call
    max_tokens_per_call = 16384  # 16,384 tokens

    # Split the content into chunks of maximum allowed tokens per API call
    chunked_content = [content[i:i + max_tokens_per_call] for i in range(0, len(content), max_tokens_per_call)]

    for i, chunk in enumerate(chunked_content):
        training_data = [{"role": "user", "content": text} for text in chunk]
        training_data.extend([{"role": "user", "content": prompt[0]} for prompt in example_prompts])
        training_data.extend([{"role": "assistant", "content": prompt[1]} for prompt in example_prompts])

        num_tokens = num_tokens_from_messages(training_data, model="gpt-3.5-turbo-16k")
        if num_tokens > max_tokens_per_call:
            print(num_tokens)
            raise ValueError("The number of tokens exceeds the maximum allowed per API call.")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=training_data,
        )

        print(f"Chunk {i + 1}/{len(chunked_content)} completed.")


def customer_service_chat(prompt):
    openai.api_key = credentials.api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": prompt}],
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
    url = "https://www.takumi-duesseldorf.de/"
    desired_tokens = 16000  # Set the desired number of tokens for content extraction
    content, remaining_tokens = crawl_website(url, remaining_tokens=desired_tokens)

    with open("output.txt", "w", encoding="utf-8") as txt_file:
        for item in content:
            txt_file.write(item + "\n")
    print("Done!")
    # Webhook test
    train_chatgpt_model(content)
    app.run(debug=True)

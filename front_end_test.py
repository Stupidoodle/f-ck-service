from flask import Flask, render_template, request
import random

app = Flask(__name__)


def customer_service_chat(prompt):
    response = ["1", "2", "3", "4"]
    return random.randint(0, len(response))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prompt = request.form["prompt"]
        response = customer_service_chat(prompt)
        return render_template("index.html", prompt=prompt, response=response)
    return render_template("index.html", prompt="", response="")

if __name__ == "__main__":
    app.run(debug=True)

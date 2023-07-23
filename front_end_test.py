from flask import Flask, render_template, request, jsonify
    
import random

app = Flask(__name__)

def customer_service_chat(prompt):
    response = ["1", "2", "3", "4"]
    return random.choice(response)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        prompt = data.get("prompt", "")
        response = customer_service_chat(prompt)
        return jsonify({"response": response})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

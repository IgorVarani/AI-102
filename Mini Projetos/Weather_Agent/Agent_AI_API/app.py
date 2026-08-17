from flask import Flask, render_template, request
from tools import get_weather
app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def home():
    data = None
    if request.method == "POST":
        cidade = request.form.get("cidade")

        print("CIDADE RECEBIDA:", cidade)

        if cidade:
            data = get_weather(cidade)

    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug = True)
    
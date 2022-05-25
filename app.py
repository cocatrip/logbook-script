from flask import Flask, render_template, request
from logbook import fill_logbook
import uuid
import os

app = Flask(__name__)
app_root = os.path.dirname(os.path.abspath(__file__))


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    target = os.path.join(app_root, 'data')
    if not os.path.isdir(target):
        os.makedirs(target)

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        file = request.files["file"]
        filename = str(uuid.uuid4()) + ".csv"
        destination = '/'.join([target, filename])
        file.save(destination)
        fill_logbook(email, password, destination)
        return render_template("done.html")


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

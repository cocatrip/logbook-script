from flask import Flask, render_template, request
from logbook import fill_logbook
import uuid
import os

app = Flask(__name__)
app_root = os.path.dirname(os.path.abspath(__file__))


@app.route('/upload', methods=['POST'])
def upload():
    # return render_template("loading.html")

    target = os.path.join(app_root, 'data')
    if not os.path.isdir(target):
        os.makedirs(target)

    email = request.form["email"]
    password = request.form["password"]
    file = request.files["file"]
    filename = str(uuid.uuid4()) + ".csv"
    destination = '/'.join([target, filename])
    file.save(destination)
    return render_template("loading.html", email=email, password=password, destination=destination)


@app.route("/run", methods=['POST'])
def run():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.json
        email = data["email"]
        password = data["password"]
        destination = data["destination"]
        fill_logbook(email, password, destination)
        return "filled!"
    else:
        return 'Content-Type not supported!'


@app.route("/done")
def done():
    return render_template("done.html")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)

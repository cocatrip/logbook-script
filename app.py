from flask import (Flask, render_template, request,
                   Response, send_from_directory)
from logbook import fill_logbook
import os

app = Flask(__name__)
app_root = os.path.dirname(os.path.abspath(__file__))


@app.route('/upload', methods=['POST'])
def upload():
    email = request.form["email"]
    password = request.form["password"]
    strm = request.form["strm"]
    sheet_id = request.form["sheet_id"]
    sheet_name = request.form["sheet_name"]

    return render_template(
        "loading.html", email=email, password=password,
        sheet_id=sheet_id, sheet_name=sheet_name, strm=strm)


@app.route("/run", methods=['POST'])
def run():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        data = request.json
        email = data["email"]
        password = data["password"]
        strm = data["strm"]
        sheet_id = data["sheet_id"]
        sheet_name = data["sheet_name"]

        def generate():
            for row in fill_logbook(email, password, strm, sheet_id, sheet_name):
                yield row + '\n'
        return Response(generate(), mimetype='text/html')
    else:
        return "Content-Type not supported!"


@app.route("/done")
def done():
    return render_template("done.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)

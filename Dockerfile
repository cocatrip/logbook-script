FROM python:3.10.5-alpine

WORKDIR /usr/src/app

RUN apk add --update --no-cache build-base

COPY requirements.txt ./

RUN pip install --verbose --no-cache-dir -r requirements.txt

COPY . .

CMD [ "gunicorn", "app:app", "--bind=0.0.0.0:8000", "--keep-alive=120", "--max-requests=3" ]

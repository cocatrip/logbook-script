FROM python:3.10.7-slim-bullseye as builder

WORKDIR /usr/src/app

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./

RUN pip install --verbose --upgrade pip

RUN pip install --verbose --requirement requirements.txt


FROM python:3.10.7-slim-bullseye

WORKDIR /usr/src/app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

ENTRYPOINT [ "gunicorn", "app:app", "--bind=0.0.0.0:8080", "--keep-alive=120", "--max-requests=3" ]

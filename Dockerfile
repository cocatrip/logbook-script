FROM amancevice/pandas:alpine as builder

WORKDIR /usr/src/app

RUN apk add --update --no-cache build-base

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./

RUN pip install --verbose --upgrade pip

RUN pip install --verbose --requirement requirements.txt


FROM python:3.10.5-alpine

WORKDIR /usr/src/app

RUN apk add --update --no-cache libstdc++

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

ENTRYPOINT [ "gunicorn", "app:app", "--bind=0.0.0.0:8000", "--keep-alive=120", "--max-requests=3" ]

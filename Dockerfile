FROM python:3.8

COPY . /app

WORKDIR /app

RUN mkdir __logger

# install google chrome and chromedriver
RUN echo "===> Installing system dependencies..." \
    && apt update && apt upgrade -y && apt install -y python3 python3-pip \
    wget software-properties-common apt-transport-https ca-certificates \
    gnupg2 curl unzip xvfb libxi6 libgconf-2-4 \
    \
    && echo "===> Installing chromedriver and google-chrome..." \
    && wget -O- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg \
    && echo deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt update && apt install google-chrome-stable -y \
    \
    && wget https://chromedriver.storage.googleapis.com/2.9/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

# set display port to avoid crash
ENV DISPLAY=:99

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python", "./app.py"]

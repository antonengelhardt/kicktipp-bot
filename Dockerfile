FROM python:3.14.0a1-alpine

# install chromedriver
RUN apk update
RUN apk add chromium
RUN apk add chromium-chromedriver

WORKDIR /app

# upgrade pip
RUN pip install --upgrade pip

# copy files
COPY requirements.txt requirements.txt
COPY main.py main.py
COPY game.py game.py

# Install the Python requirements
RUN pip install -r requirements.txt

# Set display port as an environment variable
ENV DISPLAY=:99

# Run the application
CMD ["python", "main.py", "--headless"]

FROM python:3.8-alpine

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add chromium chromium-chromedriver

# upgrade pip
RUN pip install --upgrade pip
COPY . /app
WORKDIR /app

# Install the Python requirements
RUN pip install -r requirements.txt

# Set the entrypoint to run the Python script
CMD ["python", "./main.py", "headless", "withZapier"]
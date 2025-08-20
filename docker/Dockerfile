FROM python:3.10.13-alpine

# install chromedriver
RUN apk update && apk add chromium chromium-chromedriver curl && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# upgrade pip
RUN pip install --upgrade pip

# copy files
COPY requirements.txt requirements.txt
COPY src/ src/
COPY run.py run.py

# Install the Python requirements
RUN pip install -r requirements.txt

# Set display port as an environment variable
ENV DISPLAY=:99

# Expose health check port
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "run.py", "--headless"]

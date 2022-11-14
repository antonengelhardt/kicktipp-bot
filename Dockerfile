from python:3.7

COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
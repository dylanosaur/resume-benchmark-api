FROM python:3.8.5-slim-buster

COPY . /app

WORKDIR /app

RUN pip install -r /app/requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "-t", "4"]
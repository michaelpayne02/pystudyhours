FROM python:3.12.0rc1-alpine3.18
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py /etc/periodic/hourly/main.py
RUN chmod +x /etc/periodic/hourly/main.py

CMD ["crond", "-f", "-d", "8"]
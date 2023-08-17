FROM python:3.12.0rc1-alpine3.18
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

VOLUME /etc/pystudyhours

RUN echo "* * * * * python -u /app/main.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontabs/root

COPY main.py main.py

CMD ["crond", "-f", "-d", "8"]
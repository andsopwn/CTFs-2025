FROM python:3.12-slim

RUN apt-get update && apt-get install -y git socat && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password bright
USER bright
WORKDIR /home/bright

ADD ./requirements.txt /home/bright/requirements.txt
RUN pip install -r requirements.txt
ADD ./server.py /home/bright/server.py
ADD ./pow.py /home/bright/pow.py
ADD ./flag.py /home/bright/flag.py
ADD images /home/bright/images

CMD ["socat", "-T", "180", "TCP-LISTEN:12874,reuseaddr,fork", "EXEC:\"python -u /home/bright/server.py\""]

EXPOSE 12874
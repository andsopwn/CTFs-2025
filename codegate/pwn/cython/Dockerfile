FROM ubuntu:24.04

RUN apt-get update -y
RUN apt-get install -y socat

RUN useradd -mU ctf

COPY ./bin/run /home/ctf/run
COPY ./flag /home/ctf/flag

RUN chown -R root:ctf /home/ctf
RUN chmod -R 750 /home/ctf

CMD socat -T 300 TCP-LISTEN:1357,reuseaddr,fork EXEC:/home/ctf/run,su=ctf

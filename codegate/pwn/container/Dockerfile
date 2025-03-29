FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    qemu-kvm \
    qemu-system-x86 \
    qemu-utils \
    && rm -rf /var/lib/apt/lists/*


COPY share/pow.py /app/ctf_challenge.py
COPY share/bin /app/bin
COPY share/Windows11.qcow2 /app/Windows11.qcow2
COPY flag /flag

WORKDIR /app
RUN chmod +x /app/ctf_challenge.py
CMD ["python3", "/app/ctf_challenge.py"]

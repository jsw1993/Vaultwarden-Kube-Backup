FROM python:3.9.13-alpine

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY vaultwarden-backup.py /opt/vaultwarden-backup.py
WORKDIR /opt

ENTRYPOINT ["/usr/local/bin/python3", "vaultwarden-backup.py"]
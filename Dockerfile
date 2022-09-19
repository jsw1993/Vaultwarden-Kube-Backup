FROM python:3-slim

COPY pyproject.toml /app/pyproject.toml
WORKDIR /app

RUN pip install "poetry"
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY vaultwarden-kube-backup /app/vaultwarden-kube-backup

ENTRYPOINT ["/usr/local/bin/python3", "-m", "vaultwarden-kube-backup"]
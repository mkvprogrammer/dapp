FROM python:3.12-slim

WORKDIR /work

COPY infra/requirements.txt /infra/requirements.txt
RUN pip install --no-cache-dir -r /infra/requirements.txt

COPY infra/scripts/setup.py /infra/scripts/setup.py
COPY docker/setup/entrypoint.sh /entrypoint.sh
COPY docker/setup/patch_env.py /patch_env.py

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

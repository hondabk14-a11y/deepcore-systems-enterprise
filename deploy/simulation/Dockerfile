# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY deploy/simulation/requirements.txt /app/requirements.txt
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then PIP_CERT=/run/secrets/ca_bundle pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir -r requirements.txt; fi \
    && useradd --uid 10001 --create-home simulator && mkdir /data && chown simulator:simulator /data
COPY CORE/deepcore_runtime.py CORE/deepcore_crypto.py CORE/deepcore_key_registry.py CORE/deepcore_consensus.py CORE/binance_observer.py /app/CORE/
COPY SIMULATION/local_server.py /app/SIMULATION/local_server.py
COPY deploy/simulation/binance-snapshot.json /app/binance-snapshot.json
USER simulator
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "SIMULATION.local_server", "--host", "0.0.0.0", "--state-dir", "/data", "--market-snapshot", "/app/binance-snapshot.json"]

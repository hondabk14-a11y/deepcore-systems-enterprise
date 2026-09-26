FROM python:3.12-slim
RUN useradd --create-home --uid 1000 bkillings
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=1000:1000 protocol.py storage.py key_store.py node.py cluster_demo.py benchmark.py /app/
COPY --chown=1000:1000 tests /app/tests
USER 1000
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 deepcore
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=1000:1000 CORE /app/CORE
COPY --chown=1000:1000 SERVICES /app/SERVICES
COPY --chown=1000:1000 deployment.json /app/deployment.json
USER 1000
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/readyz', timeout=4)"
CMD ["python", "-m", "uvicorn", "SERVICES.reference_api:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1", "--no-proxy-headers"]

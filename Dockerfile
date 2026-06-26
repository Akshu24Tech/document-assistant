FROM python:3.11-slim

WORKDIR /code

# install deps first so this layer caches when only app code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# chroma + history db live here; mount a volume to keep them between restarts
RUN mkdir -p data logs
VOLUME ["/code/data"]

EXPOSE 8000
# shell form so $PORT (injected by Render) is honoured; falls back to 8000 locally
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

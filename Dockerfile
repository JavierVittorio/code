FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# opencv (pulled in by rapidocr) needs these shared libs even in headless use
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Warm the OCR engine once at build time so the first request doesn't pay model init.
RUN python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()"

COPY docext/ docext/
COPY api/ api/
COPY eval/ eval/
COPY tools/__init__.py tools/calibrate.py tools/
ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

RUN useradd -m -u 1000 app && mkdir -p /app/.cache /app/outputs && chown -R app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

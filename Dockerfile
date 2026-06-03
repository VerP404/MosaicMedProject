FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_ENV=prod \
    DAGSTER_HOME=/app/mosaic_conductor/dagster_home

WORKDIR /app

# netcat — wait-for-db; gcc — psycopg2; libs — Playwright Chromium + Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    gcc \
    libpq-dev \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt

# base.txt уже содержит dash/dbc; dash_dn/requirements.txt конфликтует (dbc<2 vs ==2.0.3)
RUN pip install --upgrade pip \
    && pip install -r requirements/base.txt \
    && pip install "playwright>=1.44,<2" \
    && playwright install --with-deps chromium

COPY . /app

RUN mkdir -p /app/logs /app/uploads /app/mosaic_conductor/dagster_home/storage \
    && chmod +x /app/docker/entrypoint.sh /app/docker/start-services.sh

EXPOSE 8000 5000 5001 5020 3000 7777

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["/app/docker/start-services.sh"]

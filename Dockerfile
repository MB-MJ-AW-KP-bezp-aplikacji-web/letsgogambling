
FROM node:20-slim AS css-builder

WORKDIR /build

COPY package.json tailwind.config.js ./
COPY static/ ./static/
COPY templates/ ./templates/
COPY casino/ ./casino/

RUN npm install && npm run build:css


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r casino && useradd -r -g casino casino

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Copy built Tailwind CSS from builder stage
COPY --from=css-builder /build/static/css/tailwind.out.css /app/static/css/tailwind.out.css

# Create staticfiles directory for collectstatic
RUN mkdir -p /app/staticfiles

RUN chmod +x /app/entrypoint.sh && chown -R casino:casino /app

# Switch to non-root user
USER casino

EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000').read()" || exit 1

CMD [ "/app/entrypoint.sh" ]

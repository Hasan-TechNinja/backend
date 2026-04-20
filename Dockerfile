# Base image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV DJANGO_SETTINGS_MODULE=skincare.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make build-essential \
    libpq-dev python3-dev \
    libjpeg-dev zlib1g-dev \
    libssl-dev libffi-dev \
    curl git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files (at build time, or run this separately)
RUN python manage.py collectstatic --noinput || true

# Expose Django port
EXPOSE 8000

# Default command (start Daphne server)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "skincare.asgi:application"]

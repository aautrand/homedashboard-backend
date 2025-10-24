# Use a small Python base image
FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
 && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip \
    && pip install poetry


# Copy only necessary files first to cache dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of your application code
COPY . .

# Tell Flask where your app lives
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8050

# Expose the default Flask port
EXPOSE 8050

# Use Gunicorn for production‐grade serving
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:app"]
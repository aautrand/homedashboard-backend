# Use a small Python base image
FROM python:3.11-slim

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
ENV FLASK_RUN_PORT=8000

# Expose the default Flask port
EXPOSE 5000

# Use Gunicorn for production‐grade serving
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
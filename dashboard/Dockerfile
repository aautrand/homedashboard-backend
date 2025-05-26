FROM python:3.11-slim

# Install Poetry
RUN pip install --upgrade pip \
    && pip install poetry

# Set working directory
WORKDIR /app

# Copy only necessary files first to cache dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the code
COPY .. .

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose Flask port
EXPOSE 5000

# Run Flask using Poetry’s environment
CMD ["flask", "run"]

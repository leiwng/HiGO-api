# /Dockerfile
# Stage 1: Build stage with dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Set environment variables to prevent caching of pip packages
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_NO_INTERACTION=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app
COPY ./pet_breed_0dd7f7.json .
COPY ./.env .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use Gunicorn for production with Uvicorn workers for performance
# The number of workers can be adjusted based on the server's CPU cores
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

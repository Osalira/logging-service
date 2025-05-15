# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directory for logs
RUN mkdir -p logs

# Ensure scripts are executable
RUN chmod +x /app/entrypoint.sh && \
    chmod +x /app/init-db-once.sh && \
    dos2unix /app/entrypoint.sh && \
    dos2unix /app/init-db-once.sh

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Use our entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 
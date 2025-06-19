# Use the official Python image with 3.12 (as required by your pyproject.toml)
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*


# Install uv (fast dependency installer for pyproject.toml)
RUN pip install uv

# Copy only dependency files first for caching
COPY pyproject.toml uv.lock ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy the rest of the code
COPY . ./


# Set the entrypoint to use the PORT env variable (default 8080)
CMD python server.py
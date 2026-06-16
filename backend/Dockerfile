# ================= BUILDER STAGE =================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install virtualenv and build dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ================= RUNTIME STAGE =================
FROM python:3.12-slim AS runtime

WORKDIR /workspace

# Install postgres client library runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Setup application environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace

# Create a non-privileged user to execute application commands
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /workspace

# Copy backend files and change ownership
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Default command launches Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

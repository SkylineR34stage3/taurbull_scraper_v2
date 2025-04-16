FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create cache directory
RUN mkdir -p cache

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["python", "src/main.py"] 
# Use Python 3.10 base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for MongoDB Atlas SSL
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the app
COPY . .

# Expose Flask default port (optional)
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]

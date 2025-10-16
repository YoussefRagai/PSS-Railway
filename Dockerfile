# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything into container
COPY . .

# Install dependencies (if you have requirements.txt inside backend/)
RUN pip install --no-cache-dir -r backend/requirements.txt || true

# Expose port (change if your app uses another)
EXPOSE 8000

# Run backend as default process
CMD ["python", "backend/main.py"]

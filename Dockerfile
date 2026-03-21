FROM python:3.11-slim

WORKDIR /app

# Copy all project files first (for proper module resolution)
COPY . .

# Set PYTHONPATH to include /app
ENV PYTHONPATH=/app

# Install dependencies
RUN pip install --no-cache-dir -r saas/requirements.txt

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "saas.app:app", "--host", "0.0.0.0", "--port", "8000"]

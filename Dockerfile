# Dockerfile for AQI FastAPI Project
# 1. Use official Python image
FROM python:3.11-slim

# 2. Set work directory
WORKDIR /app



# 4. Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY ./app/ ./app

# 6. Expose port (default for uvicorn)
EXPOSE 8000

# 7. Set environment variables (optional, can be overridden)
ENV PYTHONUNBUFFERED=1

# 8. Run the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

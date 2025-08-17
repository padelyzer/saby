FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main_trading_bot_fly.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main_trading_bot_fly.py"]
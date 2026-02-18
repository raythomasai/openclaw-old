# Use a lightweight Python base
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements or just the necessary script
# Since we have a venv locally, we'll just install the core needs in the container
RUN pip install --no-cache-dir \
    requests \
    python-dotenv \
    py-clob-client \
    eth-account \
    eth-abi

# Copy the strategy script and .env
COPY strategy.py .
COPY .env .

# Run the script
CMD ["python", "strategy.py"]

FROM python:3.13-slim

WORKDIR /app

# Copy the entire project first
COPY . /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run when container starts
ENTRYPOINT ["python", "mcp_server.py"]
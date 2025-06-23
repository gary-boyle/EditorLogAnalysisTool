# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /

# Copy files
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

# Run the app
CMD ["python", "main.py"]

# Use a base Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY main.py .

# Specify the command to run your script
CMD ["python", "-u", "main.py"]
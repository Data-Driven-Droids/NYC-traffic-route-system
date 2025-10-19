# Use an official Python 3.13 runtime as a parent image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the file that lists your project's dependencies
COPY requirements.txt .

# Install those dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project code (like main.py) into the container
COPY . .

# Tell Docker what command to run when the container starts
CMD ["python", "main.py"]
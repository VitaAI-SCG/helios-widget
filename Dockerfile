# Use an official lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the harvester script into the container
COPY helios_harvester.py .

# Command to run when the container starts
CMD ["python", "helios_harvester.py"]
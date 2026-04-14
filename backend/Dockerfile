# Start from official Python 3.12 slim image
FROM python:3.12-slim

# Create a non-root user for the app to run as
RUN groupadd -r pca && useradd -r -g pca -d /app -s /sbin/nologin pca

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the ownership of the application files to the non-root user
RUN chown -R pca:pca /app

# Switch to the non-root user
USER pca

# Expose the port the application will run on
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]

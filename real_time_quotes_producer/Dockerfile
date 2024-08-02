# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=real_time_quotes_producer.settings
ENV PYTHONUNBUFFERED=1

# Expose port 8000 for the Django application
EXPOSE 8003

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"]

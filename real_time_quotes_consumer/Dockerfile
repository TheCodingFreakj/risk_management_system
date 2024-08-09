# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install  -r requirements.txt
RUN pip install --upgrade pip
# Copy the rest of the application code into the container
COPY . /app/

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=real_time_quotes_consumer.settings
ENV PYTHONUNBUFFERED=1

# Expose port 8000 for the Django application
EXPOSE 8002

# # Copy entrypoint script
COPY entrypoint.sh /code/entrypoint.sh

# # Make the script executable
RUN chmod +x /code/entrypoint.sh

# # Set the entrypoint
ENTRYPOINT ["/code/entrypoint.sh"]

# # Run the Django development server
# CMD ["daphne", "-b", "0.0.0.0", "-p", "8002", "real_time_quotes_consumer.asgi:application"]
# # CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]

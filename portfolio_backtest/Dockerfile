# Use your custom Lean Engine image as the base image
FROM leanengine-v3:latest

# Install Python and pip
# Install Python, pip, PostgreSQL client, wget, and .NET runtime
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    postgresql-client 
    # wget \
    # apt-transport-https \
    # && wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    # && dpkg -i packages-microsoft-prod.deb \
    # && apt-get update \
    # && apt-get install -y dotnet-runtime-5.0


# Create a symlink to ensure `python` command is available
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Set environment variables for Django and PostgreSQL connection
ENV DJANGO_SETTINGS_MODULE=portfolio_backtest.settings
ENV PYTHONUNBUFFERED=1
ENV POSTGRES_DB=defaultdb
ENV POSTGRES_USER=avnadmin
ENV POSTGRES_PASSWORD=AVNS_18I1eywxzSMn0TaBzxw
ENV POSTGRES_HOST=pg-6dd75e5-priyaarshinipallavi-3893.g.aivencloud.com
ENV POSTGRES_PORT=22585
ENV POSTGRES_SCHEMA=stocks_schema

# Expose port 8011 for the Django application
EXPOSE 8011
RUN chmod +x /app/startup.sh
# Set the entry point to run the Lean Engine
ENTRYPOINT ["/app/startup.sh"]

# # Default command to run the Django server; this can be overridden by the user
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8011"]



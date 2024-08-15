# Stage 1: Build .NET environment
FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS dotnet_base
WORKDIR /app

# Copy the Lean application into the .NET container
COPY Lean/ /app/Lean/

# Stage 2: Build Python environment
FROM python:3.9-slim AS python_base

# Install Python dependencies
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 3: Build final image with both .NET SDK and Python
FROM python:3.9-slim AS final

# Install necessary packages for .NET SDK installation
RUN apt-get update && \
    apt-get install -y wget apt-transport-https gnupg && \
    wget https://packages.microsoft.com/keys/microsoft.asc && \
    apt-key add microsoft.asc && \
    wget https://packages.microsoft.com/config/debian/10/prod.list && \
    mv prod.list /etc/apt/sources.list.d/dotnet.list && \
    apt-get update && \
    apt-get install -y dotnet-sdk-6.0 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the Lean application from the .NET base stage
COPY --from=dotnet_base /app/Lean /app/Lean

# Copy Python application code and dependencies from the Python base stage
COPY --from=python_base /app /app

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=trading_platform.settings
ENV PYTHONUNBUFFERED=1

# Expose port 8010 for the Django application
EXPOSE 8010

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8010"]

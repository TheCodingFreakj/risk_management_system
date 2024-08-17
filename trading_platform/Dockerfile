# Start with an official Python image
FROM python:3.9-slim

# # Install dependencies needed for Docker
# RUN apt-get update && \
#     apt-get install -y \
#     curl \
#     lsb-release \
#     gnupg \
#     software-properties-common \
#     apt-transport-https \
#     ca-certificates && \
#     curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
#     echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
#     apt-get update && \
#     apt-get install -y docker-ce docker-ce-cli containerd.io

# # Install Docker Compose
# RUN curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
#     chmod +x /usr/local/bin/docker-compose

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Set permissions on the docker-compose.yaml and entrypoint.sh
# RUN chmod +x /app/docker-compose.yaml
RUN chmod +x /app/entrypoint.sh

# Expose port 8010 for the Django application
EXPOSE 8010

# Set the entry point to the script
CMD ["/app/entrypoint.sh"]

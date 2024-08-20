# Use the official .NET SDK 6.0 image as a base for building the project
FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build-env

# Set environment variables
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_RUNTIME=coreclr  
ENV PYTHONNET_PYDLL=/usr/local/lib/libpython3.8.so


# Set the working directory
WORKDIR /Lean

# # Clone the Lean repository from GitHub
# # RUN git clone https://github.com/QuantConnect/Lean.git .
COPY ./Lean /Lean
# Verify that the project files are in the correct location
RUN ls -l /Lean

# Restore NuGet packages
RUN dotnet restore /Lean/QuantConnect.Lean.sln 
# Restore NuGet packages and build the solution, including all C# projects
# RUN dotnet restore QuantConnect.Lean.sln
RUN dotnet build QuantConnect.Lean.sln -c Release --output /Lean/build 
COPY config.json /Lean/build/
# Install dependencies for building Python
RUN apt-get update && \
    apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses-dev \
    libffi-dev \
    libsqlite3-dev \
    libreadline-dev \
    libbz2-dev \
    liblzma-dev \
    && apt-get clean

# Download and install Python 3.8
RUN wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz && \
    tar xzf Python-3.8.10.tgz && \
    cd Python-3.8.10 && \
    ./configure --enable-optimizations --enable-shared && \
    make altinstall && \
    rm -rf /Python-3.8.10.tgz /Python-3.8.10


# Search for libpython3.8.so and create a symlink if needed
RUN find / -name "libpython3.8.so" 2>/dev/null

# Verify that the Python shared library exists
RUN ls -l /usr/local/lib/libpython3.8.so


# Set LD_LIBRARY_PATH to include /usr/local/lib
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# Install pip for Python 3.8
RUN python3.8 -m ensurepip --upgrade && \
    python3.8 -m pip install --upgrade pip setuptools wheel
 
# Install Python.NET
RUN python3.8 -m pip install pythonnet

# Debugging: Check the PythonNET_PYDLL value and file existence
RUN echo "PYTHONNET_PYDLL is set to: $PYTHONNET_PYDLL" && ls -l $PYTHONNET_PYDLL   
# RUN pip3 install --no-cache-dir -r /Lean/Algorithm.Python/requirements.txt

RUN echo "import clr; print('Python.NET is working correctly')" > test_pythonnet.py && \
    python3.8 test_pythonnet.py

RUN apt-get update && \
    apt-get install -y libgomp1 libatlas-base-dev libblas-dev liblapack-dev && \
    python3.8 -m pip install numpy pandas matplotlib scipy quantconnect    
# # Use the official .NET Runtime 6.0 image as a base for running the application
FROM mcr.microsoft.com/dotnet/runtime:6.0

# Set environment variables
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_PYDLL=/usr/local/lib/libpython3.8.so

# Set the working directory
WORKDIR /Lean
# Create the Cache directory
RUN mkdir -p /Lean/Cache
RUN echo "dummy cache file" > /Lean/Cache/dummy.txt
# Copy the built files from the previous stage
# COPY --from=build-env /Lean/build/* /Lean/
COPY --from=build-env /Lean /Lean
COPY --from=build-env /Lean/build/*.dll /Lean/
COPY --from=build-env /Lean/build/*.exe /Lean/
COPY --from=build-env /Lean/build/*.json /Lean/
# Copy the rest of the Lean directory (including Python scripts)
COPY --from=build-env /Lean/Algorithm.Python /Lean/Algorithm.Python
# Verify the config.json file is in the final build directory
RUN echo "Checking if config.json is in the final /Lean/build directory:" && ls -l /Lean/config.json
RUN echo "Checking if MovingAverageCrossAlgorithm.py is in the final /Lean/Algorithm.Python directory:" && ls -l /Lean/Algorithm.Python

# Verify the contents of the root directory
RUN echo "Checking contents of /Lean directory:" && ls -l /Lean

# Define the entry point for the Docker container
CMD ["dotnet", "/Lean/QuantConnect.Lean.Launcher.dll"]

docker run -it <your-docker-image-name> /bin/bash






"parameters": {
        "Stock": "AAPL",
        "ShortMAPeriod": "20",
        "LongMAPeriod": "50",
        "StartDate": "2020-01-01",
        "EndDate": "2023-01-01",
        "InitialCash": "200000"
    },
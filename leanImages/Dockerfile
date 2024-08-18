# Stage 1: Mono installation in an isolated stage using Ubuntu
FROM ubuntu:20.04 AS mono-env

# Set environment variable to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu
# Install dependencies for Mono and libjpeg8
RUN apt-get update && \
    apt-get install -y wget gnupg dirmngr ca-certificates apt-transport-https \
    libjpeg8 libpng-dev libtiff-dev libgif-dev && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF && \
    echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | tee /etc/apt/sources.list.d/mono-official-stable.list && \
    apt-get update && \
    apt-get install -y mono-complete && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Find and set the correct path for libmonosgen-2.0.so.1
RUN find / -name "libmonosgen-2.0.so.1" 2>/dev/null
# Stage 2: Python and .NET setup in another isolated stage using Ubuntu
FROM ubuntu:20.04 AS python-dotnet-env

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_RUNTIME=coreclr  
ENV PYTHONNET_PYDLL=/usr/local/lib/libpython3.8.so
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu

# Set PYTHONPATH to ensure the Lean Python modules are accessible
ENV PYTHONPATH=/Lean/Algorithm.Python:/Lean/Launcher

# Install Mono to ensure libmono is available
RUN apt-get update && \
    apt-get install -y wget gnupg dirmngr ca-certificates apt-transport-https \
    libjpeg8 libpng-dev libtiff-dev libgif-dev && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF && \
    echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | tee /etc/apt/sources.list.d/mono-official-stable.list && \
    apt-get update && \
    apt-get install -y mono-complete && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies for Python and .NET SDK
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev zlib1g-dev libncurses-dev \
    libffi-dev libsqlite3-dev libreadline-dev libbz2-dev liblzma-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download and install Python 3.8
RUN wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz && \
    tar xzf Python-3.8.10.tgz && \
    cd Python-3.8.10 && \
    ./configure --enable-optimizations --enable-shared && \
    make altinstall && \
    rm -rf /Python-3.8.10.tgz /Python-3.8.10

# Verify that libpython3.8.so exists
RUN find /usr/local/lib -name "libpython3.8.so" -print || echo "libpython3.8.so not found!"
RUN chmod 755 /usr/local/lib/libpython3.8.so
# Verify that the library and environment variables are correctly set up
RUN ls -l /usr/local/lib  # Check that the library file is in the expected location
RUN env  # List all environment variables to verify they are set correctly

# Run a simple test to check if the library can be loaded
RUN python3.8 -c "import ctypes; ctypes.CDLL('/usr/local/lib/libpython3.8.so')"


# Install pip for Python 3.8
RUN python3.8 -m ensurepip --upgrade && \
    python3.8 -m pip install --upgrade pip setuptools wheel

# Install Python.NET
RUN python3.8 -m pip install pythonnet==2.5.2

# Install necessary Python packages like pandas
RUN python3.8 -m pip install pandas numpy matplotlib scipy quantconnect

# Verify Python.NET installation
RUN python3.8 -m pip show pythonnet  # <-- Add this line here to verify installation


# Debugging: Check the PythonNET_PYDLL value and file existence
RUN echo "PYTHONNET_PYDLL is set to: $PYTHONNET_PYDLL" && ls -l $PYTHONNET_PYDLL

# Add the test script
RUN echo "import clr; clr.AddReference('System'); from System import DateTime; print('Current DateTime from .NET:', DateTime.Now)" > test_pythonnet.py

# Run the test script
RUN python3.8 test_pythonnet.py

# Stage 3: Combine Mono and Python/.NET environments and build the project using the .NET SDK
FROM mcr.microsoft.com/dotnet/sdk:6.0-focal AS build-env

# Set environment variables
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_PYDLL=/usr/local/lib/libpython3.8.so
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu

# Set PYTHONPATH to ensure the Lean Python modules are accessible
ENV PYTHONPATH=/Lean/Algorithm.Python:/Lean/Launcher

# Reinstall libselinux1 to fix the library version issue
RUN apt-get update && \
    apt-get install --reinstall -y libselinux1

# Set the working directory
WORKDIR /Lean

# Copy Mono installation from the first stage
COPY --from=mono-env /usr/lib/mono /usr/lib/mono
COPY --from=mono-env /usr/lib/cli /usr/lib/cli
COPY --from=mono-env /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=mono-env /usr/lib/libmonosgen-2.0.so.1 /usr/lib/libmonosgen-2.0.so.1
COPY --from=mono-env /usr/lib/x86_64-linux-gnu/libmono* /usr/lib/x86_64-linux-gnu/
COPY --from=mono-env /usr/lib/libmono* /usr/lib/
COPY --from=mono-env /usr/bin/mono* /usr/bin/
COPY --from=mono-env /usr/share/mono /usr/share/mono

# Copy Python and .NET setup from the second stage
COPY --from=python-dotnet-env /usr/local /usr/local

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/Lean/Algorithm.Python  

RUN rm -f /Lean/Algorithm.Python/MovingAverageAlgorithm.py
# Ensure the old files are removed
RUN rm -rf /Lean/Algorithm.Python/DynamicMovingAverageAlgorithm.py


# Copy the Lean directory from the local machine to the Docker container
COPY ./Lean /Lean

# After installing everything, verify the environment
RUN echo "import sys; print(sys.path)" > /Lean/Algorithm.Python/test_env.py
RUN python3.8 /Lean/Algorithm.Python/test_env.py

# Verify that the algorithm file exists
RUN ls -l /Lean/Algorithm.Python/DynamicMovingAverageAlgorithm.py

# Verify that the project files are in the correct location
RUN ls -l /Lean || true
# Verify that the .NET SDKs are installed correctly
RUN dotnet --list-sdks  
# Verify that Python.NET is installed
RUN python3.8 -m pip list | grep pythonnet 
# Restore NuGet packages
RUN dotnet restore /Lean/QuantConnect.Lean.sln

# Build the solution, including all C# projects
RUN dotnet build QuantConnect.Lean.sln -c Release --output /Lean/build 

# Copy config.json to the build directory
COPY config.json /Lean/build/

# Use the same .NET SDK image for running the application to keep the environment consistent
FROM mcr.microsoft.com/dotnet/sdk:6.0-focal

# Copy Python installation from the second stage
COPY --from=python-dotnet-env /usr/local/bin/python3.8 /usr/local/bin/python3.8
COPY --from=python-dotnet-env /usr/local/lib/libpython3.8* /usr/local/lib/
COPY --from=python-dotnet-env /usr/local/include/python3.8 /usr/local/include/python3.8
COPY --from=python-dotnet-env /usr/local/lib/python3.8 /usr/local/lib/python3.8
COPY --from=python-dotnet-env /usr/local/bin/pip3 /usr/local/bin/pip3

# Set environment variables
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_PYDLL=/usr/local/lib/libpython3.8.so
ENV PYTHONPATH=/Lean/Algorithm.Python:/Lean
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu

COPY --from=mono-env /usr/lib/mono /usr/lib/mono
COPY --from=mono-env /usr/lib/libmono* /usr/lib/
COPY --from=mono-env /usr/lib/libmonosgen-2.0.so.1 /usr/lib/libmonosgen-2.0.so.1
COPY --from=mono-env /usr/lib/x86_64-linux-gnu/libmono* /usr/lib/x86_64-linux-gnu/
COPY --from=mono-env /usr/bin/mono* /usr/bin/
COPY --from=mono-env /usr/share/mono /usr/share/mono
# Set the working directory
WORKDIR /Lean

# Create the Cache directory
RUN mkdir -p /Lean/Cache
RUN echo "dummy cache file" > /Lean/Cache/dummy.txt

# Copy the built files from the previous stage
COPY --from=build-env /Lean /Lean
COPY --from=build-env /Lean/build /Lean/
# COPY --from=build-env /Lean/build/*.dll /Lean/
# COPY --from=build-env /Lean/build/*.exe /Lean/
# COPY --from=build-env /Lean/build/*.json /Lean/
# Copy the rest of the Lean directory (including Python scripts)
COPY --from=build-env /Lean/Algorithm.Python /Lean/Algorithm.Python

# Set permissions for the MovingAverageCrossAlgorithm.py file
RUN chmod 644 /Lean/Algorithm.Python/DynamicMovingAverageAlgorithm.py

# Verify the config.json file is in the final build directory
RUN echo "Checking if config.json is in the final /Lean/build directory:" && ls -l /Lean/build/config.json
RUN echo "Checking if DynamicMovingAverageAlgorithm.py is in the final /Lean/Algorithm.Python directory:" && ls -l /Lean/Algorithm.Python

# Verify the contents of the root directory
RUN echo "Checking contents of /Lean directory:" && ls -l /Lean


# Add debugging steps
# Print environment variables
RUN echo "Printing environment variables before running Lean:" && env

# List the contents of critical directories
RUN echo "Listing /usr/local/lib directory:" && ls -l /usr/local/lib
RUN echo "Listing /Lean/Algorithm.Python directory:" && ls -l /Lean/Algorithm.Python

# Verify that the Python modules are in the expected location
RUN echo "Python paths:" && python3.8 -c "import sys; print(sys.path)"
RUN ls -l /Lean/Algorithm.Python


# Verify that the project files are in the correct location
RUN ls -l /Lean

# # Add a script to test Python.NET integration
# RUN echo "import clr; clr.AddReference('System'); from System import DateTime; print('Current DateTime from .NET:', DateTime.Now)" > test_pythonnet.py
# RUN python3.8 test_pythonnet.py


# Define the entry point for the Docker container
CMD ["dotnet", "/Lean/QuantConnect.Lean.Launcher.dll"]










# Stage 1: Build environment
FROM mcr.microsoft.com/dotnet/sdk:6.0-focal AS build-env

ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_PYDLL=/usr/lib/x86_64-linux-gnu/libpython3.8.so
ENV PYTHONPATH=/Lean/Algorithm.Python:/Lean
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu:/usr/lib/libmono-2.0.so.1
ENV PYTHONNET_RUNTIME=coreclr

# # Copy the Lean directory from the local machine to the Docker container
COPY ./Lean /Lean


# Restore NuGet packages and build the solution
RUN dotnet restore /Lean/QuantConnect.Lean.sln && \
    dotnet build /Lean/QuantConnect.Lean.sln -c Release --output /Lean/build
 


# Clean up unnecessary files and reduce image size
RUN apt-get purge -y git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.nuget /root/.dotnet

# Stage 2: Final image
# FROM mcr.microsoft.com/dotnet/sdk:6.0-focal AS final
FROM mcr.microsoft.com/dotnet/aspnet:6.0-focal AS final


# Add Microsoft package repository for .NET
RUN apt-get update && \
    apt-get install -y wget apt-transport-https && \
    wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-6.0 \
    && rm -rf /var/lib/apt/lists/*

ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV LC_ALL=C.UTF-8
ENV PYTHONNET_PYDLL=/usr/lib/x86_64-linux-gnu/libpython3.8.so
ENV PYTHONPATH=/Lean/Algorithm.Python:/Lean
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/mono:/usr/lib/x86_64-linux-gnu:/usr/lib/libmono-2.0.so.1
ENV PYTHONNET_RUNTIME=coreclr

WORKDIR /Lean

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip mono-runtime python3.8 python3.8-dev libpython3.8 libpython3.8-dev && \
    rm -rf /var/lib/apt/lists/*

 # Find and display the path of libpython3.8.so
RUN find / -name "libpython3.8.so"

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir setuptools wheel pythonnet pandas numpy quantconnect && \
    rm -rf ~/.cache/pip

# Copy necessary runtime files from the build stage
COPY --from=build-env /Lean/build /Lean/
COPY --from=build-env /Lean /Lean/

# Set proper permissions for the entire Lean directory
RUN chmod -R 755 /Lean
RUN ls -l /Lean/Data/alternative/interest-rate/usa/interest-rate.csv

RUN ls -l /Lean/Data/equity/usa/
RUN rm -rf /Lean/Launcher/bin /Lean/Launcher/build-output
RUN rm -rf /Lean/Tests/ \
           /Lean/Documentation/ \
           /Lean/Research/ \
           /Lean/Optimizer/ \
           /Lean/ToolBox/ \
           /Lean/VisualStudio/ \
           /Lean/Algorithm.FSharp/ \
           /Lean/bin/ \
           /Lean/obj/ \
           /Lean/.vscode/ \
           /Lean/.idea/ \
           /Lean/.env \
           /Lean/*.user \
           /Lean/*.suo \
        #    /Lean/Data/daily/ \
        #    /Lean/Data/minute/ \
        #    /Lean/Data/tick/ \
        #    /Lean/Data/alternative/ \
           /Lean/lib/
COPY config.json /Lean/config.json
RUN find / -name "libpython3.8.so" 2>/dev/null
# Final cleanup to reduce image size
RUN apt-get purge -y --auto-remove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache /usr/share/doc /usr/share/man /usr/share/locale /usr/share/info /usr/share/gnome/help

# Set the entry point for the Docker container
CMD ["dotnet", "QuantConnect.Lean.Launcher.dll", "--config", "config.json"]



































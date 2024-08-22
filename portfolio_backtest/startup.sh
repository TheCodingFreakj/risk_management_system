#!/bin/bash

# Run the Lean Engine with the specified configuration
dotnet /Lean/QuantConnect.Lean.Launcher.dll --config /Lean/config-algo1.json
# Increase verbosity to capture more debug information
export VERBOSE=true
# Check if the Lean Engine process was successful
if [ $? -eq 0 ]; then
   
    echo "Lean Engine completed successfully. Starting Django server..."
    
    # Start the Django development server
    python manage.py runserver 0.0.0.0:8011
else
    echo "Lean Engine encountered an error. Exiting."
    exit 1
fi

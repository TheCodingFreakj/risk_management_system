import logging

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set this to the desired level for your application

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # Set this to the desired level for your application

# Create file handler for profiling logs
fh = logging.FileHandler('profiling.log')
fh.setLevel(logging.DEBUG)  # Set this to the desired level for profiling logs

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to handlers
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

# Suppress Kafka library logs below WARNING level
logging.getLogger('kafka').setLevel(logging.WARNING)  # Suppress Kafka logs lower than WARNING

# Optionally, suppress other verbose libraries if needed
# logging.getLogger('another_library').setLevel(logging.WARNING)


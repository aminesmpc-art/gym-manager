# Gunicorn configuration file
import multiprocessing

# Worker configuration
workers = 1  # Reduced to 1 to prevent OOM
threads = 2
worker_class = 'gthread'

# Timeout configuration - CRITICAL for Railway
timeout = 120
graceful_timeout = 120
keepalive = 5

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# Server socket
bind = '0.0.0.0:8080'

# Preload (disabled to save memory)
preload_app = False

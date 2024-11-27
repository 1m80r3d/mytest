# gunicorn_config.py

bind = "0.0.0.0:8000"  # Bind to all interfaces on port 8000
workers = 1           # Number of worker processes (adjust as needed, or mkr in )
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn as the worker class

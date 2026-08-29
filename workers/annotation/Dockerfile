# Set the base image and install cron
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install cron and dependencies from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Stage 5: consume annotation_queue. -I/--include imports tasks.py (this
# directory is /app, already on sys.path) so annotation.annotate_article
# actually registers on the shared app before the worker starts consuming —
# shared/celery_app.py itself only defines the app, not the tasks.
# --concurrency=2: a single local Ollama instance doesn't meaningfully
# parallelize inference anyway — more worker slots than Ollama can actually
# run at once just queue up on its side, so this keeps things simple rather
# than pretending to be more concurrent than the backing LLM actually is.
CMD ["celery", "-A", "shared.celery_app", "worker", "-Q", "annotation_queue", "--loglevel=info", "--concurrency=2", "-I", "tasks"]


#/////////////////////////////////////////////////
# # Set the base image and install cron
# FROM python:3.11-slim-bookworm

# # Set the working directory
# WORKDIR /app

# # Copy the current directory contents into the container at /app
# COPY . .

# # Install cron and dependencies from requirements.txt
# RUN python -m venv /opt/venv && \
#     /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
#     /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# # CMD to start cron
# CMD ["/opt/venv/bin/python", "main.py"]

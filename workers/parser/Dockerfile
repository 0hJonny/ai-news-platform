# Set the base image and install cron
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install cron and dependencies from requirements.txt
RUN apt-get update && apt-get -y install cron \
    # && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    # && apt install ./google-chrome-stable_current_amd64.deb -y \
    # && rm google-chrome-stable_current_amd64.deb \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && rm -rf /root/.cache/pip /var/cache/apt/*

# Copy the cronjob file to the /etc/cron.d/ directory and set permissions
# (kept for reference / manual use — `cron -f` still works if you override
# CMD — but Stage 5's default is the Celery worker below instead of the
# old scheduled full-scrape run.)
COPY cronjob /etc/cron.d/cronjob
RUN chmod 0644 /etc/cron.d/cronjob

# Stage 5: consume parsing_queue. -I/--include imports tasks.py (this
# directory is /app, already on sys.path) so parsing.scrape_source actually
# registers on the shared app before the worker starts consuming —
# shared/celery_app.py itself only defines the app, not the tasks.
# --concurrency=2: default (CPU count) hammers the target site with that
# many parallel requests at once — cloudscraper's own per-instance
# Cloudflare-challenge solve isn't free either. A real crawler should be
# polite about request rate regardless of target; 2 keeps things moving
# without tripping 429s from a real site the way 10 did.
CMD ["celery", "-A", "shared.celery_app", "worker", "-Q", "parsing_queue", "--loglevel=info", "--concurrency=2", "-I", "tasks"]

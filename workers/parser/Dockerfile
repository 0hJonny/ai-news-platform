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
COPY cronjob /etc/cron.d/cronjob
RUN chmod 0644 /etc/cron.d/cronjob

# CMD to start cron
CMD ["cron", "-f"]

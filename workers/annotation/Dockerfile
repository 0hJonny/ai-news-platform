# Set the base image and install cron
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install cron and dependencies from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# CMD to start cron
CMD ["tail", "-f", "/dev/null"]


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

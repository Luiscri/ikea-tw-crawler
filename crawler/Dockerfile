# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim-bullseye

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Get APP_PORT from arguments
ARG APP_PORT

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
CMD exec gunicorn --bind :$APP_PORT --workers 1 --threads 8 --timeout 0 main:app
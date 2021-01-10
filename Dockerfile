FROM python:3.8-slim

LABEL maintainer="tsore28@wgu.edu"

USER root

RUN python -m pip install gunicorn

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN python -m pip install -r requirements.txt

COPY . /app

# Create the application user and group
RUN groupadd -r bikeshare && useradd -r -s /bin/false -g bikeshare user

# Change ownership of the app folder from root to the new user
RUN chown -R user:bikeshare /app

# Set all Files to be read only and allow execute
RUN chmod -R 551 /app/*

# allow write on the plots directory
RUN chmod u=rwx /app/static/images/plots

# Run as the new user
USER user

# Run application on gunicorn WSGI server with port 8000 - log to standard out
ENTRYPOINT gunicorn -c gunicorn_config.py app:app

# Use an official Python runtime as the base image
FROM python:3.10.4-buster

# Set the working directory in the container
WORKDIR /opt/project

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH .

# Install dependencies
RUN set -xe \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY ["requirements.txt", "./"]
RUN pip install -r requirements.txt
RUN mkdir -p /opt/project/staticfiles
RUN mkdir -p /opt/project/mediafiles

# Copy project files
COPY . .

# Expose the Django development server port (adjust if needed)
EXPOSE 8000

# Set up the entrypoint
RUN chmod a+x scripts/entrypoint.sh

ENTRYPOINT ["/bin/sh", "scripts/entrypoint.sh"]
# Use a Playwright image matching your project's version
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Install Xvfb for a virtual display
RUN apt-get update && apt-get install -y xvfb

WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Copy all code into /app
COPY . /app

# Ensure Python doesn't buffer output so logs appear immediately
ENV PYTHONUNBUFFERED=1

# Run Python under Xvfb
CMD ["xvfb-run", "--server-args=-screen 0 1024x768x24", "python", "-u", "main.py"]

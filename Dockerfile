FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the rest of the application code
COPY . .

# Expose port 8050 (Default Dash port)
EXPOSE 8050

# Set the environment variable for the app version number
ENV APP_VERSION=$APP_VERSION

# Run the application using Gunicorn
CMD ["python", "--bind", "0.0.0.0:8050", "app:server"]
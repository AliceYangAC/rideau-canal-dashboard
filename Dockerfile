FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# We assume gunicorn is not in requirements.txt, so we add it explicitly
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the rest of the application code
COPY . .

# Expose port 8050 (Default Dash port)
EXPOSE 8050

# Define environment variables to be passed at runtime
# (These are placeholders; actual values must be provided during run)
ENV COSMOS_CONN_STR=""
ENV COSMOS_KEY=""
ENV BLOB_CONN_STR=""
ENV PORT=8050

# Run the application using Gunicorn
# 'app:server' tells Gunicorn to look in 'app.py' for the 'server' object
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:server"]
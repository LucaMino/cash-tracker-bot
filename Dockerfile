FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Install dependencies required to create virtualenv
RUN pip install --no-cache-dir virtualenv

# Create a virtual environment in the /app/venv directory
RUN python -m venv /app/venv

# Create a non-root user
RUN useradd -m myuser

# Set permissions for /app so myuser can access it
RUN chown -R myuser:myuser /app

# Switch to the non-root user
USER myuser

# Activate virtual environment by adding it to PATH
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements.txt and install dependencies inside the virtual environment
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code to /app/src/
COPY src/ /app/src/

# Run the bot.py script with the virtual environment
CMD ["python", "src/bot.py"]

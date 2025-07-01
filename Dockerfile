FROM python:3.9-slim

# set work dir
WORKDIR /app

# copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY src/ /app/src/

# run bot.py
CMD ["python", "src/bot.py"]
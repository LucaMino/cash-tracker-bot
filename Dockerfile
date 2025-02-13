FROM python:3.9-slim

# set work dir
WORKDIR /app

# install dependecies from requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

# run bot.py
CMD ["python", "src/bot.py"]
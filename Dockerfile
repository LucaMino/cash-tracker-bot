FROM python:3.9-slim

# set work dir
WORKDIR /app

# install venv
RUN python -m venv venv

# install dependecies from requirements.txt
COPY requirements.txt /app/
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

# run bot.py
CMD ["venv/bin/python", "src/bot.py"]
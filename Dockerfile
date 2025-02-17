FROM python:3.9-slim

# set work dir
WORKDIR /app

# install virtualenv
RUN pip install virtualenv

# create a virtual environment
RUN virtualenv venv

# activate the virtual environment and install dependencies from requirements.txt
COPY requirements.txt /app/
RUN . venv/bin/activate && pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

# run bot.py
CMD ["venv/bin/python", "src/bot.py"]
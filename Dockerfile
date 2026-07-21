FROM python:3.14


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app

COPY .env /code/.env


CMD ["uvicorn", "app.main:socket_app", "--reload", "--host", "0.0.0.0", "--port", "8003"]
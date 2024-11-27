#------------------------------------------------------------------------------------------------------------------
FROM python:3.12 AS base

RUN echo "deb http://deb.debian.org/debian/ unstable main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev && apt-get clean
#------------------------------------------------------------------------------------------------------------------
FROM base AS app

RUN pip install --no-cache-dir "poetry"
COPY ./pyproject.toml ./poetry.lock* /app/
WORKDIR /app/
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi
COPY ./src/app /app/app
ENV PYTHONPATH=/app
ENV IMG_PATH="/data/"

CMD [ "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "app/config/gunicorn_config.py", "app.main:app"]
#------------------------------------------------------------------------------------------------------------------
FROM app AS test
COPY ./src/tests /app/tests
ENV IMG_PATH="/app/tests/test_data/"

CMD [ "pytest" ]

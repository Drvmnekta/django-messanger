FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV POETRY_VERSION=${POETRY_VERSION:-1.2.0}

ENV WORKERS=${WORKERS:-1}
ENV HOST=${HOST:-0.0.0.0}
ENV PORT=${PORT:-8000}

ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"messenger.messenger.settings"}

WORKDIR /opt

RUN apt-get update && apt-get install -y libssl-dev swig python3-dev gcc make
RUN pip install --upgrade pip && pip install poetry==$POETRY_VERSION

COPY poetry.lock pyproject.toml README.md ./

RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-cache --without=dev

COPY messenger ./messenger

RUN poetry build -f wheel
RUN pip install dist/messenger-*.whl --no-deps
RUN rm -rf *

#COPY makefile.docker ./makefile

ENTRYPOINT gunicorn messenger.messenger.wsgi --workers $WORKERS --bind $HOST:$PORT
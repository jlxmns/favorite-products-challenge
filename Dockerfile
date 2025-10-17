FROM python:3.13-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /code

WORKDIR /code

RUN pip install poetry

COPY pyproject.toml poetry.lock /code/

RUN poetry config virtualenvs.create false

RUN poetry install --only main --no-root --no-interaction

COPY . /code

WORKDIR /code

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

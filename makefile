install:
	poetry install --no-root

run:
	python3 manage.py runserver

migrate:
	python3 manage.py migrate

lint:
	poetry run flake8 .

mami:
	python3 manage.py makemigrations

locale:
	python3 manage.py compilemessages

run-0:
	python3 manage.py runserver 0.0.0.0:8000
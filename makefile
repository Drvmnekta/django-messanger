install:
	poetry install --no-root

run:
	python3 messenger.manage.py runserver

migrate:
	python3 messenger.manage.py migrate

lint:
	poetry run flake8 messenger

mami:
	python3 messenger.manage.py makemigrations

locale:
	python3 messenger.manage.py compilemessages

run-0:
	python3 messenger.manage.py runserver 0.0.0.0:8000

collectstatic:
	python3 -m messenger.manage collectstatic -n
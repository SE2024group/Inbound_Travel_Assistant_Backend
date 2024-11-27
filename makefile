# Makefile

run:
	python manage.py runserver

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic --noinput

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

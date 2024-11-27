install:
	poetry install

uninstall:
	poetry remove --all

update:
	poetry update

test:
	cd src && poetry run pytest

run:
	cd src && poetry run uvicorn app.main:app --reload

build:
	docker build --tag crop .

build_app:
	docker build --target app --tag crop_app .

run_docker:
	docker run -v ${PWD}/satellite_images:/data -p 8000 -i -t crop_app:latest

run_docker_shell:
	docker run -v ${PWD}/satellite_images:/data -p 8000 -i -t crop:latest /bin/bash
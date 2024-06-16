IMAGE_NAME = antonengelhardt/kicktipp-bot:amd64

all: docker-build docker-push

local-run:
	python main.py --local

local-run-with-zapier:
	python main.py --local

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-push:
	docker push $(IMAGE_NAME)

docker-build-and-push: docker-build docker-push

docker-run:
	docker run -it --name $(IMAGE_NAME) --platform linux/amd64 --env-file .env $(IMAGE_NAME)

docker-reset:
	docker stop $(IMAGE_NAME)
	docker rm $(IMAGE_NAME)

docker-all: docker-build-and-push docker-reset docker-run

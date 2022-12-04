IMAGE_NAME = antonengelhardt/kicktipp-bot

all: docker-build docker-push 

local-run:
	python3 main.py local

local-run-with-zapier:
	python3 main.py local withZapier

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-push:
	docker push $(IMAGE_NAME)

docker-build-and-push: docker-build docker-push

docker-run:
	docker run -it --name $(IMAGE_NAME) -e KICKTIPP_EMAIL=$(KICKTIPP_EMAIL) -e KICKTIPP_PASSWORD=$(KICKTIPP_PASSWORD) -e KICKTIPP_NAME_OF_COMPETITION=$(KICKTIPP_NAME_OF_COMPETITION) -e ZAPIER_URL=$(ZAPIER_URL) $(IMAGE_NAME)

docker-reset:
	docker stop $(IMAGE_NAME)
	docker rm $(IMAGE_NAME)

docker-all: docker-build-and-push docker-reset docker-run
.PHONY: clean build_image

run:
	@./scripts.sh run

build_image:
	@./scripts.sh build_image tallulah/backend

run_image:
	@./scripts.sh run_image

stop_all:
	@./scripts.sh stop_all

stop_backend:
	@./scripts.sh stop_backend

push_image: build_image
	@./scripts.sh push_image_to_registry tallulah/backend
	@./scripts.sh push_image_to_registry tallulah/rabbitmq
	@./scripts.sh push_image_to_registry tallulah/mongo

generate_client:
	@./scripts.sh generate_client

deploy: push_image
	@./devops/deploy.sh

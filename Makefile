IMAGES = tallulah/backend tallulah/rabbitmq tallulah/logstash

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

push_all: $(IMAGES)
$(IMAGES):
	@echo "Pushing image: $@"
	@./scripts.sh push_image_to_registry $@

.PHONY: push_all $(IMAGES)

generate_client:
	@./scripts.sh generate_client

deploy:
	@./scripts.sh deploy

release:
	@./scripts.sh release

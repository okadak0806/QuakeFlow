.PHONY: container-image lint publish-container-image

# Customize the variables as desired/required
CONTAINER_IMAGE_NAME=kfp-tutorial-count-rows-component:v000
# _ORG=elyra
DH_ORG=okadak86

QUAY_ORG=elyra

SKIP_LINT ?= false

lint:
ifeq ($(SKIP_LINT),false)
	pip install -r test-requirements.txt
	flake8 .
endif

container-image: lint  ## Build component container image
	docker build -t $(CONTAINER_IMAGE_NAME) .

# blish-container-image: publish-container-image-quay publish-container-image-dh
publish-container-image:  publish-container-image-dh
	# handled by dependencies

# publish-container-image-quay: container-image ## Publish component container image on quay.io
# 	docker tag $(CONTAINER_IMAGE_NAME) quay.io/$(QUAY_ORG)/$(CONTAINER_IMAGE_NAME)
# 	docker push quay.io/$(QUAY_ORG)/$(CONTAINER_IMAGE_NAME)
# 	docker inspect --format="{{index .RepoDigests 0}}" quay.io/$(QUAY_ORG)/$(CONTAINER_IMAGE_NAME)

publish-container-image-dh: container-image ## Publish component container image on hub.docker.com
	docker tag $(CONTAINER_IMAGE_NAME) docker.io/$(DH_ORG)/$(CONTAINER_IMAGE_NAME)
	docker push docker.io/$(DH_ORG)/$(CONTAINER_IMAGE_NAME)
	docker inspect --format="{{index .RepoDigests 0}}" docker.io/$(DH_ORG)/$(CONTAINER_IMAGE_NAME)

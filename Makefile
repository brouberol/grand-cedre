.PHONY: clean build

clean:
	find -type d -name __pycache__ | xargs rm -r || true

build: clean
	pytest
	docker build -t brouberol/grand-cedre .

push: build
	git stash || true
	docker push brouberol/grand-cedre
	git stash pop || true

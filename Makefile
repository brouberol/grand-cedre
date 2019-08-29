.PHONY: clean build

clean:
	find -type d -name __pycache__ | xargs rm -r || true

build: clean
	docker build -t brouberol/grand-cedre .

push: build
	git stash
	docker push brouberol/grand-cedre
	git stash pop

.PHONY: test build upload clean

all:
	@echo "usage: make [test | build | upload | clean]"

test:
	pytest --log-cli-level=DEBUG

build:
	python3 -m pip install --upgrade build
	python3 -m build

upload:
	python3 -m twine upload dist/*

clean:
	rm dist/*

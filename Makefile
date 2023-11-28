.PHONY: test-offline test-api-live build upload clean

all:
	@echo "usage: make [test | build | upload | clean]"

test-offline:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

test-api-live:
	pytest --log-cli-level=DEBUG

build:
	python3 -m pip install --upgrade build
	python3 -m build

upload:
	python3 -m twine upload dist/*

clean:
	rm dist/*

.PHONY: venv


venv:
	. venv/bin/activate \

test:
	python setup.py test


pytest:
	. venv/bin/activate \
	pytest

VENV=./venv
VENV_BIN=${VENV}/bin
VENV_PYTHON=${VENV_BIN}/python
VENV_PYTEST=${VENV_BIN}/pytest

.PHONY: venv


venv:
	. venv/bin/activate \

test:
	${VENV_PYTHON} setup.py test


pytest:
	${VENV_PYTEST}

PYTHON := python
VIRTUALENV := virtualenv
VENV_DIR := venv
PIP := pip

all:
	$(MAKE) -C fasttextdb

test:
	$(PYTHON) -m unittest discover

install:
	$(MAKE) -C fasttextdb
	$(PIP) install .

virtualenv: $(VENV_DIR)

$(VENV_DIR): requirements.txt
	$(VIRTUALENV) -p python3 $@
	$@/bin/pip install -r $<

clean:
	-rm *.pyc
	-rm -r __pycache__
	$(MAKE) -C fasttextdb clean
	$(MAKE) -C tests clean

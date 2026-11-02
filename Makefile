PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test check doctor

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) -m orbis_3d.cli.main check $(VIDEO)

doctor:
	$(PYTHON) -m orbis_3d.cli.main doctor

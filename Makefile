test:
	python3 -m unittest discover -s tests -t . -v

serve:
	python3 -m src.server

experiment:
	python3 -m experiments.probe_experiment

compare:
	python3 -m experiments.compare_experiment

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: test serve experiment compare clean

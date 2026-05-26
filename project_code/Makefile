.PHONY: install test exp1 exp2 plots all docker-build k8s-apply k8s-delete clean

install:
	pip install -r requirements.txt

test:
	python3 -m unittest discover -s tests -v

exp1:
	python3 experiments/exp1_variance_vs_k.py

exp2:
	python3 experiments/exp2_movement_on_removal.py

plots:
	python3 plots/make_plots.py

# Run everything endto end
all: test exp1 exp2 plots

docker-build:
	docker build -t dspy-node:latest .

k8s-apply:
	kubectl apply -f k8s/dspy.yaml

k8s-delete:
	kubectl delete -f k8s/dspy.yaml

clean:
	rm -f experiments/results_*.csv plots/*.png
	find . -type d -name __pycache__ -exec rm -rf {} +

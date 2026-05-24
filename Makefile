.PHONY: install check ingest transform features orchestrate run test

install:
	pip install .

check:
	PYTHONPATH=. python scripts/check_setup.py

ingest:
	PYTHONPATH=. python pipeline/ingest.py

transform:
	PYTHONPATH=. python pipeline/transform.py

features:
	PYTHONPATH=. python pipeline/features.py

orchestrate:
	PYTHONPATH=. python pipeline/orchestrate.py

run:
	PYTHONPATH=. streamlit run dashboard/app.py --browser.gatherUsageStats false

test:
	pytest tests/

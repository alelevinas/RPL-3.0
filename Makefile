.PHONY: install test dev lint clean

install:
	pip install -r base_requirements.txt -r rpl_activities/extra_requirements.txt -r rpl_users/extra_requirements.txt

test:
	python -m pytest

dev:
	# Run both microservices using uvicorn
	(trap 'kill 0' SIGINT; 
	 uvicorn rpl_users.src.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir rpl_users/src & 
	 uvicorn rpl_activities.src.main:app --host 0.0.0.0 --port 8001 --reload --reload-dir rpl_activities/src)

lint:
	python -m flake8 rpl_activities/src rpl_users/src

seed:
	@echo "Seeding backend data..."
	python scripts/seed_dev_data.py --students 5 --courses 2 --activities-per-course 3 --bulk-submissions

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

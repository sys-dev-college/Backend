.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")

down_db:
	docker compose -f docker-compose-dev.yml down -v

up_db:
	docker compose -f docker-compose-dev.yml up -d

.PHONY: test
test:
	$(ENV_PREFIX)pytest -v --cov-config .coveragerc --cov=app -l --tb=short --maxfail=1 tests/
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

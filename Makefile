.PHONY: up down test eval lint

up:
	docker compose up --build -d

down:
	docker compose down

test:
	.\.venv\Scripts\python.exe -m pytest apps/api/tests apps/worker/tests -v

eval:
	.\.venv\Scripts\python.exe -m eval.run_kb_eval

lint:
	.\.venv\Scripts\python.exe -m ruff check apps/

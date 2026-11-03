.PHONY: up down

up:
	@test -f .env || { echo "copy .env.example to .env first"; exit 1; }
	docker compose up -d --wait

down:
	docker compose down

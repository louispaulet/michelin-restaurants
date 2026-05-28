.PHONY: up kill test build deploy data refresh

PORT ?= 5173

up:
	@if [ ! -d node_modules ]; then npm install; fi
	@mkdir -p .tmp
	@nohup sh -c 'tail -f /dev/null | ./node_modules/.bin/vite --host 0.0.0.0 --port "$$1"' _ $(PORT) > .tmp/vite.log 2>&1 & echo $$! > .tmp/vite.pid
	@echo "Vite running at http://localhost:$(PORT)/michelin-restaurants/"

kill:
	@if [ -f .tmp/vite.pid ]; then kill $$(cat .tmp/vite.pid) 2>/dev/null || true; rm -f .tmp/vite.pid; fi
	@pkill -f "vite.*$(PORT)" 2>/dev/null || true
	@echo "Stopped Vite dev server on port $(PORT)."

data:
	python3 scripts/generate_restaurants_csv.py

refresh:
	@if [ -s public/data/restaurants.csv ]; then \
		echo "Restaurant list already exists at public/data/restaurants.csv; skipping refresh."; \
	else \
		$(MAKE) data; \
	fi

test:
	npm test

build:
	npm run build

deploy:
	npm run deploy

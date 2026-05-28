# Restaurant descriptions pipeline

This project can generate original restaurant descriptions from review/source material in two phases:

1. collect source material per restaurant into `.tmp/reviews/<restaurant-id>.json`;
2. prepare and submit an OpenAI Batch API JSONL file that asks for one synthetic summary per restaurant.

## Source policy

Use only public, crawlable pages or official APIs. The collector is intentionally conservative:

- Michelin Guide page from the existing `michelin_url`.
- The restaurant's official website from the existing `website` field.
- Optional Brave Search API snippets when `BRAVE_SEARCH_API_KEY` is set.
- Optional Google Places API place details/reviews when `GOOGLE_MAPS_API_KEY` is set.

Do not copy review text into the public app. Source excerpts are temporary inputs for generating an original synthesis and are written under `.tmp/`, which is git-ignored.

Generated summaries should be neutral, editorial, and based only on the collected source material. If a restaurant has sparse source material, generate a conservative description rather than inventing facts.

## Typical workflow

```bash
# Pilot one restaurant
python3 scripts/collect_restaurant_reviews.py --restaurant-id 114-faubourg
python3 scripts/prepare_description_batch.py --restaurant-id 114-faubourg

# Full run
python3 scripts/collect_restaurant_reviews.py --all
python3 scripts/prepare_description_batch.py --all --allow-empty
python3 scripts/submit_openai_batch.py .tmp/openai/description_batch.jsonl
python3 scripts/fetch_openai_batch_results.py .tmp/openai/batch_metadata.json
python3 scripts/validate_descriptions.py data/restaurant_descriptions.json
python3 scripts/apply_descriptions.py data/restaurant_descriptions.json
```

`submit_openai_batch.py` and `fetch_openai_batch_results.py` require `OPENAI_API_KEY` in the environment.

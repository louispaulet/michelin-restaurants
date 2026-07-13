# Project Instructions

- Always read `AGENTS.md` before starting any task in this repository.
- If `AGENTS.md` cannot be found at the project root, assume it does not exist and suggest creating one.
- Always commit and push after each change, even when working directly on the `main` branch.
- Prefer small, focused changes that keep the app deployable through GitHub Pages.
- Run relevant verification before committing. For app changes, prefer `make test` and `make build`.

## Product and data contract

- This is a static Vite + React explorer backed exclusively by the generated Wikidata snapshot in `public/data`.
- Include every restaurant entity returned by the auditable `P166 = Q20824563` query. `P4160` is optional, and no restaurant may be silently dropped during generation.
- Do not add fallbacks, inferred values, scraped Michelin data, geocoding, generated descriptions, or source blending. Missing Wikidata fields must stay explicitly missing.
- Do not invent one-, two-, or three-star tiers. Use “Michelin star award recorded in Wikidata” unless the data contract changes.
- Preserve the immediate Wikidata locality even when it is a borough, ward, district, or neighborhood.
- A canonical city must come from the `P131` hierarchy and descend from city (`Q515`). Reject the sub-city classes documented in `metadata.json`, continue to a qualifying parent city, and leave the city missing when none exists.

## Implementation workflow

- Keep the public routes and `HashRouter` deployment model compatible with GitHub Pages.
- Treat `scripts/wikidata_restaurants.sparql` and `scripts/generate_restaurants_csv.py` as the auditable data pipeline. Refresh with `make data`; the generator must remain atomic and fail closed.
- When changing grouping or generation, add fixture tests that preserve restaurant IDs, row counts, coordinates, and source membership.
- For data or app changes, run `make test` and `make build`. For documentation-only changes, at minimum run `git diff --check` and verify documented commands and paths against the repository.
- Deploy only from a clean, tested build with `make deploy`, then verify the custom domain on both desktop and mobile when the task includes deployment.

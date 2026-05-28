import { Database, Github, Star } from 'lucide-react';

export default function AboutPage() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded border border-stone-200 bg-white p-6 shadow-panel">
        <h2 className="text-3xl font-semibold">About this project</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded border border-stone-200 p-4">
            <Database className="text-michelin" />
            <h3 className="mt-3 font-semibold">Generated data</h3>
            <p className="mt-2 text-sm text-stone-600">
              The CSV is generated from Wikidata using Michelin star awards and Michelin Restaurants IDs.
            </p>
          </div>
          <div className="rounded border border-stone-200 p-4">
            <Star className="text-brass" />
            <h3 className="mt-3 font-semibold">Star tiers</h3>
            <p className="mt-2 text-sm text-stone-600">
              Current tiers are best-effort enriched from Michelin guide pages when the public page exposes them.
            </p>
          </div>
          <div className="rounded border border-stone-200 p-4">
            <Github className="text-ink" />
            <h3 className="mt-3 font-semibold">Static site</h3>
            <p className="mt-2 text-sm text-stone-600">
              The app uses hash routing so every page works when served from GitHub Pages.
            </p>
          </div>
        </div>
        <div className="mt-8 space-y-4 text-stone-700">
          <p>
            Discovery uses Wikidata property <code className="rounded bg-stone-100 px-1">P166</code> for award received,
            Michelin star item <code className="rounded bg-stone-100 px-1">Q20824563</code>, and Michelin Restaurants ID{' '}
            <code className="rounded bg-stone-100 px-1">P4160</code>.
          </p>
          <p>
            Map tiles are provided by OpenStreetMap contributors. Restaurant metadata may lag Michelin's current guide
            if upstream Wikidata records have not yet been updated.
          </p>
        </div>
      </div>
    </section>
  );
}

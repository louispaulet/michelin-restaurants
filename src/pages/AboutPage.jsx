import { Database, Github, MapPinOff, ShieldCheck, Star } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { useRestaurants } from '../state/RestaurantContext.jsx';

export default function AboutPage() {
  const { status, metadata, error } = useRestaurants();
  const generatedAt = metadata?.generated_at
    ? new Intl.DateTimeFormat('en', { dateStyle: 'long', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(metadata.generated_at))
    : null;

  return (
    <section className="page-shell max-w-6xl">
      <Breadcrumbs items={[{ label: 'World', to: '/' }, { label: 'About' }]} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && (
        <div className="space-y-10">
          <header className="max-w-4xl">
            <p className="eyebrow">Methodology & limitations</p>
            <h1 className="page-title">One source. No hidden recovery.</h1>
            <p className="mt-5 text-xl leading-8 text-stone-600">
              This site is an independent explorer of Wikidata records. It is not the official Michelin Guide and does not claim to be a complete list of currently awarded restaurants.
            </p>
          </header>

          <div className="grid gap-4 md:grid-cols-2">
            <InfoCard icon={<Database />} title="Wikidata only">
              Restaurant discovery and every public field come from Wikidata. There is no Wikipedia merge, Michelin scraping, geocoder, synthetic description, or Paris fallback.
            </InfoCard>
            <InfoCard icon={<ShieldCheck />} title="Exact inclusion rule">
              The query selects restaurant entities whose award received (<Code>P166</Code>) includes Michelin star (<Code>Q20824563</Code>). Michelin Restaurants ID (<Code>P4160</Code>) is optional.
            </InfoCard>
            <InfoCard icon={<MapPinOff />} title="Locations are never inferred">
              A canonical city is the nearest location (<Code>P131</Code>) classified under city (<Code>Q515</Code>) after boroughs, wards, city districts, and neighborhoods are rejected. Resolution continues to a sourced parent city; if none exists, the record remains under “City not specified in Wikidata.”
            </InfoCard>
            <InfoCard icon={<Star />} title="No invented star tiers">
              Wikidata’s generic award item does not reliably encode a current one, two, or three-star tier. The site therefore uses the precise phrase “Michelin star award recorded in Wikidata.”
            </InfoCard>
          </div>

          <section className="rounded border border-stone-200 bg-white p-6 sm:p-8" aria-labelledby="snapshot-heading">
            <p className="eyebrow">Published snapshot</p>
            <h2 id="snapshot-heading" className="section-title">Data provenance</h2>
            <p className="mt-3 text-stone-600">Generated {generatedAt ? `${generatedAt} UTC` : 'at an unavailable time'} with an atomic, fail-closed export.</p>
            <dl className="mt-6 grid gap-px overflow-hidden rounded border border-stone-200 bg-stone-200 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(metadata?.counts ?? {}).map(([key, value]) => (
                <div key={key} className="bg-paper p-4">
                  <dt className="text-xs font-semibold uppercase tracking-[0.1em] text-stone-500">{key.replaceAll('_', ' ')}</dt>
                  <dd className="font-display mt-2 text-2xl font-semibold">{value.toLocaleString()}</dd>
                </div>
              ))}
            </dl>
            <h3 className="mt-8 font-semibold">Missing fields kept visible</h3>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {Object.entries(metadata?.missing ?? {}).map(([key, value]) => (
                <div key={key} className="rounded border border-stone-200 p-4">
                  <dt className="text-sm capitalize text-stone-500">{key.replaceAll('_', ' ')}</dt>
                  <dd className="mt-1 text-xl font-semibold">{value.toLocaleString()}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="grid gap-8 border-t border-stone-200 pt-8 lg:grid-cols-2">
            <div>
              <h2 className="text-xl font-semibold">What the snapshot can—and cannot—say</h2>
              <p className="mt-3 leading-7 text-stone-600">An award statement may be historical, incomplete, or out of date. Restaurant status, opening state, tier, address, and coverage can lag reality. Use Wikidata and official restaurant sources for verification.</p>
            </div>
            <div>
              <h2 className="text-xl font-semibold">Open implementation</h2>
              <p className="mt-3 leading-7 text-stone-600">The SPARQL query, generator, fixture tests, and static site are public. Map tiles are served by OpenStreetMap and retain contributor attribution.</p>
              <a href="https://github.com/louispaulet/michelin-restaurants" target="_blank" rel="noreferrer" className="button-secondary mt-5"><Github size={18} /> View the source code</a>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

function InfoCard({ icon, title, children }) {
  return (
    <article className="rounded border border-stone-200 bg-white p-6">
      <span className="text-michelin">{icon}</span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mt-2 leading-7 text-stone-600">{children}</p>
    </article>
  );
}

function Code({ children }) {
  return <code className="rounded bg-stone-100 px-1.5 py-0.5 text-sm text-ink">{children}</code>;
}

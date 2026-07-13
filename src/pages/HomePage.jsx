import { ArrowRight, Database, MapPinned, Search, Star } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import StatusBlock from '../components/StatusBlock.jsx';
import { buildCityDirectory, buildCountryDirectory, restaurantsWithoutCountry } from '../data/explore.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

export default function HomePage() {
  const { status, restaurants, metadata, error } = useRestaurants();
  const [destination, setDestination] = useState('');
  const countries = useMemo(() => buildCountryDirectory(restaurants), [restaurants]);
  const leadingCities = useMemo(() => {
    return countries
      .flatMap((country) =>
        buildCityDirectory(country.restaurants).map((city) => ({ ...city, country })),
      )
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
      .slice(0, 8);
  }, [countries]);
  const unknownCountry = useMemo(() => restaurantsWithoutCountry(restaurants), [restaurants]);
  const normalizedSearch = destination.trim().toLowerCase();
  const visibleCountries = countries.filter((country) => {
    if (!normalizedSearch) return true;
    return (
      country.name.toLowerCase().includes(normalizedSearch) ||
      buildCityDirectory(country.restaurants).some((city) => city.name.toLowerCase().includes(normalizedSearch))
    );
  });

  return (
    <>
      <section className="border-b border-stone-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:px-8 lg:py-20">
          <div>
            <p className="eyebrow">Worldwide · Wikidata only</p>
            <h1 className="font-display mt-4 max-w-4xl text-5xl font-semibold leading-[0.98] tracking-[-0.035em] sm:text-6xl lg:text-7xl">
              Michelin-star records, explored honestly.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600 sm:text-xl">
              A fast, open directory of restaurant entities with a Michelin star award recorded in Wikidata—without hidden fallbacks or inferred locations.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <Link to="/restaurants" className="action-card">
              <Search size={20} />
              Browse every restaurant
              <ArrowRight className="ml-auto" size={19} />
            </Link>
            <Link to="/map" className="action-card action-card-dark">
              <MapPinned size={20} />
              Explore the world map
              <ArrowRight className="ml-auto" size={19} />
            </Link>
          </div>
        </div>
      </section>

      <section className="page-shell">
        <StatusBlock status={status} error={error} />
        {status === 'ready' && (
          <div className="space-y-14">
            <dl className="grid overflow-hidden rounded border border-stone-200 bg-white sm:grid-cols-2 lg:grid-cols-4">
              {[
                ['Restaurants', metadata?.counts?.restaurants ?? restaurants.length],
                ['Countries', metadata?.counts?.countries ?? countries.length],
                ['Wikidata cities', metadata?.counts?.cities ?? leadingCities.length],
                ['With coordinates', metadata?.counts?.mapped_restaurants ?? 0],
              ].map(([label, value]) => (
                <div key={label} className="border-b border-stone-200 p-5 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 lg:border-b-0 lg:border-r lg:last:border-r-0">
                  <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">{label}</dt>
                  <dd className="font-display mt-2 text-3xl font-semibold">{Number(value).toLocaleString()}</dd>
                </div>
              ))}
            </dl>

            <section aria-labelledby="countries-heading">
              <div className="grid gap-6 lg:grid-cols-[1fr_380px] lg:items-end">
                <div>
                  <p className="eyebrow">World → Country</p>
                  <h2 id="countries-heading" className="section-title">Explore by country</h2>
                  <p className="mt-3 max-w-2xl text-stone-600">Countries are ranked by the number of records in this snapshot. Every sourced country remains accessible.</p>
                </div>
                <label className="relative block">
                  <span className="mb-2 block text-sm font-semibold">Find a country or city</span>
                  <Search className="pointer-events-none absolute bottom-3 left-3 text-stone-500" size={19} />
                  <input value={destination} onChange={(event) => setDestination(event.target.value)} className="h-11 w-full rounded border border-stone-300 bg-white pl-10 pr-3 outline-none focus:border-michelin focus:ring-2 focus:ring-michelin/15" placeholder="Try Japan, Paris, New York…" />
                </label>
              </div>
              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {visibleCountries.map((country, index) => {
                  const cities = buildCityDirectory(country.restaurants);
                  return (
                    <Link key={country.slug} to={`/countries/${country.slug}`} className="group rounded border border-stone-200 bg-white p-5 transition hover:border-michelin hover:shadow-panel">
                      <div className="flex items-start gap-4">
                        <span className="font-display w-7 shrink-0 text-lg text-stone-400">{String(index + 1).padStart(2, '0')}</span>
                        <span className="min-w-0 flex-1">
                          <span className="flex items-baseline justify-between gap-3">
                            <span className="text-lg font-semibold group-hover:text-michelin">{country.name}</span>
                            <span className="shrink-0 text-sm font-semibold">{country.count}</span>
                          </span>
                          <span className="mt-2 block truncate text-sm text-stone-500">
                            {cities.length ? cities.slice(0, 3).map((city) => city.name).join(' · ') : 'No canonical city specified'}
                          </span>
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
              {visibleCountries.length === 0 && (
                <p className="mt-6 rounded border border-stone-200 bg-white p-6 text-stone-600">No Wikidata country or city matches “{destination}”.</p>
              )}
              {unknownCountry.length > 0 && !normalizedSearch && (
                <Link to="/restaurants" className="mt-4 flex min-h-11 items-center justify-between rounded border border-dashed border-stone-300 px-4 py-3 text-sm font-medium hover:border-michelin">
                  Country not specified in Wikidata
                  <span>{unknownCountry.length} restaurants</span>
                </Link>
              )}
            </section>

            <section aria-labelledby="cities-heading">
              <p className="eyebrow">Leading destinations</p>
              <h2 id="cities-heading" className="section-title">Cities with the most records</h2>
              <div className="mt-6 grid gap-px overflow-hidden rounded border border-stone-200 bg-stone-200 sm:grid-cols-2 lg:grid-cols-4">
                {leadingCities.map((city) => (
                  <Link key={`${city.country.slug}-${city.slug}`} to={`/countries/${city.country.slug}/cities/${city.slug}`} className="group bg-white p-5 hover:bg-paper">
                    <span className="font-display block text-xl font-semibold group-hover:text-michelin">{city.name}</span>
                    <span className="mt-1 block text-sm text-stone-500">{city.country.name}</span>
                    <span className="mt-5 flex items-center gap-2 text-sm font-semibold"><Star size={15} fill="currentColor" /> {city.count} records</span>
                  </Link>
                ))}
              </div>
            </section>

            <aside className="flex flex-col gap-5 rounded border border-stone-200 bg-white p-6 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-4">
                <Database className="mt-1 shrink-0 text-michelin" />
                <div>
                  <h2 className="font-semibold">A dated, auditable snapshot</h2>
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-stone-600">Wikidata is the sole metadata source. Missing values stay missing, and the generic award does not reliably encode a current star tier.</p>
                </div>
              </div>
              <Link to="/about" className="shrink-0 text-sm font-semibold text-michelin underline-offset-4 hover:underline">Read the methodology</Link>
            </aside>
          </div>
        )}
      </section>
    </>
  );
}

import { ArrowRight, MapPinned } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import RestaurantCard from '../components/RestaurantCard.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { findCountry } from '../data/explore.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

export default function CountryPage() {
  const { countrySlug } = useParams();
  const { status, restaurants, error } = useRestaurants();
  const country = status === 'ready' ? findCountry(restaurants, countrySlug) : null;

  return (
    <section className="page-shell">
      <Breadcrumbs items={[{ label: 'World', to: '/' }, { label: country?.name || 'Country' }]} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && !country && (
        <div className="empty-panel">
          <p className="eyebrow">Unknown destination</p>
          <h1 className="page-title mt-2">Country not found</h1>
          <p className="mt-3 text-stone-600">This country slug does not exist in the current Wikidata snapshot.</p>
          <Link to="/" className="button-primary mt-6">Return to the world overview</Link>
        </div>
      )}
      {country && (
        <div className="space-y-12">
          <header className="grid gap-6 border-b border-stone-200 pb-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">Country overview</p>
              <h1 className="page-title">{country.name}</h1>
              <p className="mt-3 text-lg text-stone-600">
                {country.count.toLocaleString()} restaurant records across {country.cities.length.toLocaleString()} canonical Wikidata cities.
              </p>
            </div>
            <Link to={`/map?country=${encodeURIComponent(country.slug)}`} className="button-secondary">
              <MapPinned size={18} /> View {country.name} on the map
            </Link>
          </header>

          <section aria-labelledby="city-directory-heading">
            <p className="eyebrow">{country.name} → City</p>
            <h2 id="city-directory-heading" className="section-title">City directory</h2>
            {country.cities.length > 0 ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {country.cities.map((city, index) => (
                  <Link key={city.slug} to={`/countries/${country.slug}/cities/${city.slug}`} className="group flex min-h-24 items-center gap-4 rounded border border-stone-200 bg-white p-5 transition hover:border-michelin hover:shadow-panel">
                    <span className="font-display text-lg text-stone-400">{String(index + 1).padStart(2, '0')}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-lg font-semibold group-hover:text-michelin">{city.name}</span>
                      <span className="mt-1 block text-sm text-stone-500">{city.count} restaurant{city.count === 1 ? '' : 's'}</span>
                    </span>
                    <ArrowRight className="shrink-0 text-stone-400 group-hover:text-michelin" size={19} />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="mt-6 rounded border border-stone-200 bg-white p-6 text-stone-600">No canonical city is specified in Wikidata for this country’s restaurant records.</p>
            )}
          </section>

          {country.withoutCity.length > 0 && (
            <section aria-labelledby="uncategorized-heading">
              <p className="eyebrow">Unassigned records</p>
              <h2 id="uncategorized-heading" className="section-title">City not specified in Wikidata</h2>
              <p className="mt-3 max-w-3xl text-stone-600">
                These {country.withoutCity.length.toLocaleString()} restaurants have no qualifying city in their Wikidata location hierarchy. They are intentionally not assigned to an inferred city.
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {country.withoutCity.map((restaurant) => <RestaurantCard key={restaurant.id} restaurant={restaurant} />)}
              </div>
            </section>
          )}
        </div>
      )}
    </section>
  );
}

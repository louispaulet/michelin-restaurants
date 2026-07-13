import { MapPinned } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import RestaurantCard from '../components/RestaurantCard.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { findCity } from '../data/explore.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

export default function CityPage() {
  const { countrySlug, citySlug } = useParams();
  const { status, restaurants, error } = useRestaurants();
  const { country, city } = status === 'ready' ? findCity(restaurants, countrySlug, citySlug) : { country: null, city: null };

  return (
    <section className="page-shell">
      <Breadcrumbs items={[
        { label: 'World', to: '/' },
        { label: country?.name || 'Country', to: country ? `/countries/${country.slug}` : '/' },
        { label: city?.name || 'City' },
      ]} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && !city && (
        <div className="empty-panel">
          <p className="eyebrow">Unknown destination</p>
          <h1 className="page-title mt-2">City not found</h1>
          <p className="mt-3 text-stone-600">This country and city combination does not exist in the current Wikidata snapshot.</p>
          <Link to={country ? `/countries/${country.slug}` : '/'} className="button-primary mt-6">Return to the destination directory</Link>
        </div>
      )}
      {city && (
        <div className="space-y-10">
          <header className="grid gap-6 border-b border-stone-200 pb-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="eyebrow">{country.name} · City overview</p>
              <h1 className="page-title">{city.name}</h1>
              <p className="mt-3 text-lg text-stone-600">
                {city.count.toLocaleString()} restaurant{city.count === 1 ? '' : 's'} with a Michelin star award recorded in Wikidata.
              </p>
            </div>
            <Link to={`/map?country=${encodeURIComponent(country.slug)}&city=${encodeURIComponent(city.slug)}`} className="button-secondary">
              <MapPinned size={18} /> View city map
            </Link>
          </header>
          <section aria-labelledby="city-restaurants-heading">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="eyebrow">Complete directory</p>
                <h2 id="city-restaurants-heading" className="section-title">Restaurants A–Z</h2>
              </div>
              <span className="text-sm font-medium text-stone-500">{city.count} total</span>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {city.restaurants.map((restaurant) => <RestaurantCard key={restaurant.id} restaurant={restaurant} />)}
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

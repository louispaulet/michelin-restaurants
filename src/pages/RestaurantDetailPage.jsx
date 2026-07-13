import { ExternalLink, Globe, MapPin, Star } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { useRestaurants } from '../state/RestaurantContext.jsx';

const Missing = ({ children }) => <span className="text-stone-500">{children}</span>;

export default function RestaurantDetailPage() {
  const { restaurantId } = useParams();
  const { status, restaurants, error } = useRestaurants();
  const restaurant = restaurants.find((item) => item.id === restaurantId);
  const countryPath = restaurant?.country_slug ? `/countries/${restaurant.country_slug}` : null;
  const cityPath = restaurant?.city_slug && countryPath ? `${countryPath}/cities/${restaurant.city_slug}` : null;

  const breadcrumbItems = [
    { label: 'World', to: '/' },
    restaurant?.country ? { label: restaurant.country, to: countryPath } : { label: 'Country not specified', to: '/restaurants' },
    restaurant?.city ? { label: restaurant.city, to: cityPath } : { label: 'City not specified', to: '/restaurants' },
    { label: restaurant?.name || 'Restaurant' },
  ];

  return (
    <section className="page-shell max-w-6xl">
      <Breadcrumbs items={breadcrumbItems} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && !restaurant && (
        <div className="empty-panel">
          <h1 className="page-title">Restaurant not found</h1>
          <p className="mt-3 text-stone-600">This restaurant ID does not exist in the current Wikidata snapshot.</p>
          <Link to="/restaurants" className="button-primary mt-6">Back to all restaurants</Link>
        </div>
      )}
      {restaurant && (
        <article>
          <header className="grid gap-8 border-b border-stone-200 pb-8 lg:grid-cols-[1fr_auto] lg:items-start">
            <div>
              <p className="eyebrow">Restaurant record</p>
              <h1 className="page-title max-w-4xl">{restaurant.name}</h1>
              <p className="mt-4 text-lg text-stone-600">{restaurant.cuisine || 'Cuisine not specified in Wikidata'}</p>
            </div>
            <span className="inline-flex w-fit items-center gap-2 rounded border border-brass/40 bg-brass/10 px-4 py-3 text-sm font-semibold">
              <Star size={18} fill="currentColor" /> Michelin star award recorded in Wikidata
            </span>
          </header>

          <div className="mt-8 grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-8">
              <section className="rounded border border-stone-200 bg-white p-6">
                <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-stone-500">Wikidata description</h2>
                <p className="mt-4 text-lg leading-8 text-stone-700">
                  {restaurant.description || <Missing>Description not specified in Wikidata.</Missing>}
                </p>
              </section>
              <dl className="grid gap-px overflow-hidden rounded border border-stone-200 bg-stone-200 sm:grid-cols-2">
                {[
                  ['Address', restaurant.address, 'Address not specified in Wikidata'],
                  ['Immediate locality', restaurant.locality, 'Locality not specified in Wikidata'],
                  ['Canonical city', restaurant.city, 'City not specified in Wikidata'],
                  ['Country', restaurant.country, 'Country not specified in Wikidata'],
                ].map(([label, value, missing]) => (
                  <div key={label} className="bg-white p-5">
                    <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">{label}</dt>
                    <dd className="mt-2 leading-6">{value || <Missing>{missing}</Missing>}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <aside className="space-y-5">
              {restaurant.latitude !== null && restaurant.longitude !== null ? (
                <div className="rounded border border-stone-200 bg-white p-5">
                  <MapPin className="text-michelin" />
                  <h2 className="mt-4 font-semibold">Coordinates from Wikidata</h2>
                  <p className="mt-1 text-sm text-stone-600">{restaurant.latitude.toFixed(5)}, {restaurant.longitude.toFixed(5)}</p>
                  <Link to={`/map?country=${encodeURIComponent(restaurant.country_slug)}&city=${encodeURIComponent(restaurant.city_slug)}`} className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-michelin underline-offset-4 hover:underline">Open on the explorer map</Link>
                </div>
              ) : (
                <div className="rounded border border-stone-200 bg-white p-5 text-stone-600">Coordinates not specified in Wikidata.</div>
              )}
              <div className="rounded border border-stone-200 bg-white p-5">
                <h2 className="font-semibold">Source links</h2>
                <div className="mt-4 grid gap-2">
                  {restaurant.website ? <ExternalLinkButton href={restaurant.website} icon={<Globe size={17} />}>Restaurant website</ExternalLinkButton> : <p className="py-2 text-sm text-stone-500">Website not specified in Wikidata.</p>}
                  {restaurant.michelin_url ? <ExternalLinkButton href={restaurant.michelin_url}>Michelin Guide record</ExternalLinkButton> : <p className="py-2 text-sm text-stone-500">Michelin Restaurants ID not specified in Wikidata.</p>}
                  <ExternalLinkButton href={`https://www.wikidata.org/wiki/${restaurant.wikidata_id}`}>Wikidata entity</ExternalLinkButton>
                </div>
              </div>
            </aside>
          </div>
        </article>
      )}
    </section>
  );
}

function ExternalLinkButton({ href, children, icon }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="flex min-h-11 items-center gap-2 rounded border border-stone-300 px-3 py-2 text-sm font-medium transition hover:border-michelin hover:text-michelin">
      {icon}{children}<ExternalLink className="ml-auto" size={15} />
    </a>
  );
}

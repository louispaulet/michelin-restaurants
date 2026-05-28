import { ArrowLeft, ExternalLink, Globe, MapPin, Star } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import StatusBlock from '../components/StatusBlock.jsx';
import { useRestaurants } from '../state/RestaurantContext.jsx';

export default function RestaurantDetailPage() {
  const { restaurantId } = useParams();
  const { status, restaurants, error } = useRestaurants();
  const restaurant = restaurants.find((item) => item.id === restaurantId);

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <StatusBlock status={status} error={error} />
      {status === 'ready' && !restaurant && (
        <div className="rounded border border-stone-200 bg-white p-8 shadow-panel">
          <p className="text-lg font-semibold">Restaurant not found.</p>
          <Link to="/restaurants" className="mt-4 inline-flex items-center gap-2 text-michelin">
            <ArrowLeft size={18} />
            Back to restaurants
          </Link>
        </div>
      )}
      {restaurant && (
        <article className="rounded border border-stone-200 bg-white p-6 shadow-panel">
          <Link to="/restaurants" className="inline-flex items-center gap-2 text-sm font-medium text-stone-600 hover:text-michelin">
            <ArrowLeft size={18} />
            Back to restaurants
          </Link>
          <div className="mt-6 flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-4xl font-semibold">{restaurant.name}</h2>
              <p className="mt-2 text-lg text-stone-600">{restaurant.cuisine || 'Cuisine not listed'}</p>
            </div>
            <span className="inline-flex w-fit items-center gap-2 rounded bg-brass/15 px-3 py-2 font-semibold">
              <Star size={18} fill="currentColor" />
              {restaurant.stars ? `${restaurant.stars} Michelin star${restaurant.stars === 1 ? '' : 's'}` : 'Michelin starred'}
            </span>
          </div>

          <dl className="mt-8 grid gap-4 md:grid-cols-2">
            <div className="rounded border border-stone-200 p-4">
              <dt className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-stone-500">
                <MapPin size={17} />
                Address
              </dt>
              <dd className="mt-2 text-stone-800">{restaurant.address || 'Not listed'}</dd>
            </div>
            <div className="rounded border border-stone-200 p-4">
              <dt className="text-sm font-semibold uppercase tracking-wide text-stone-500">Area</dt>
              <dd className="mt-2 text-stone-800">{restaurant.arrondissement || 'Not listed'}</dd>
            </div>
          </dl>

          {restaurant.description && (
            <section className="mt-8 rounded border border-stone-200 bg-stone-50 p-5">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-500">About this restaurant</h3>
              <p className="mt-3 leading-7 text-stone-700">{restaurant.description}</p>
            </section>
          )}

          <div className="mt-8 flex flex-wrap gap-3">
            {restaurant.website && (
              <a href={restaurant.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded bg-ink px-4 py-3 text-sm font-medium text-white">
                <Globe size={17} />
                Website
              </a>
            )}
            {restaurant.michelin_url && (
              <a href={restaurant.michelin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded border border-stone-300 px-4 py-3 text-sm font-medium">
                Michelin guide
                <ExternalLink size={16} />
              </a>
            )}
            {restaurant.wikidata_url && (
              <a href={restaurant.wikidata_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded border border-stone-300 px-4 py-3 text-sm font-medium">
                Wikidata
                <ExternalLink size={16} />
              </a>
            )}
          </div>
        </article>
      )}
    </section>
  );
}

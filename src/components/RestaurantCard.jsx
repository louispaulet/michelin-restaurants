import { MapPin, Star } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function RestaurantCard({ restaurant }) {
  return (
    <article className="group flex h-full flex-col rounded border border-stone-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-stone-300 hover:shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to={`/restaurants/${restaurant.id}`} className="text-xl font-semibold hover:text-michelin">
            {restaurant.name}
          </Link>
          <p className="mt-1 text-sm text-stone-600">{restaurant.cuisine || 'Cuisine not specified in Wikidata'}</p>
        </div>
        <span className="flex shrink-0 items-center gap-1 rounded bg-brass/15 px-2 py-1 text-sm font-semibold text-stone-900">
          <Star size={15} fill="currentColor" />
          Michelin
        </span>
      </div>
      <p className="mt-4 flex gap-2 text-sm text-stone-700">
        <MapPin size={17} className="mt-0.5 shrink-0 text-michelin" />
        <span>
          {restaurant.address || restaurant.locality || restaurant.city || restaurant.country || 'Location not specified in Wikidata'}
        </span>
      </p>
      <p className="mt-2 text-xs font-medium uppercase tracking-wide text-stone-500">
        {[restaurant.city, restaurant.country].filter(Boolean).join(' · ') || 'Country and city not specified in Wikidata'}
      </p>
      <div className="mt-auto pt-5">
        <Link to={`/restaurants/${restaurant.id}`} className="inline-flex min-h-11 items-center rounded bg-ink px-4 py-2 text-sm font-medium text-white transition group-hover:bg-michelin">
          View details
        </Link>
      </div>
    </article>
  );
}

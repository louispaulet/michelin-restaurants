import { ExternalLink, MapPin, Star } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function RestaurantCard({ restaurant }) {
  return (
    <article className="rounded border border-stone-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to={`/restaurants/${restaurant.id}`} className="text-xl font-semibold hover:text-michelin">
            {restaurant.name}
          </Link>
          <p className="mt-1 text-sm text-stone-600">{restaurant.cuisine || 'Cuisine not listed'}</p>
        </div>
        <span className="flex shrink-0 items-center gap-1 rounded bg-brass/15 px-2 py-1 text-sm font-semibold text-stone-900">
          <Star size={15} fill="currentColor" />
          {restaurant.stars ? `${restaurant.stars}` : 'Michelin'}
        </span>
      </div>
      <p className="mt-4 flex gap-2 text-sm text-stone-700">
        <MapPin size={17} className="mt-0.5 shrink-0 text-michelin" />
        <span>{restaurant.address || restaurant.arrondissement || 'Paris, France'}</span>
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to={`/restaurants/${restaurant.id}`} className="rounded bg-ink px-3 py-2 text-sm font-medium text-white">
          View details
        </Link>
        {restaurant.michelin_url && (
          <a
            href={restaurant.michelin_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded border border-stone-300 px-3 py-2 text-sm font-medium"
          >
            Michelin
            <ExternalLink size={14} />
          </a>
        )}
      </div>
    </article>
  );
}

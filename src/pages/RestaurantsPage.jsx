import { useMemo, useState } from 'react';
import RestaurantCard from '../components/RestaurantCard.jsx';
import RestaurantFilters from '../components/RestaurantFilters.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { filterRestaurants, uniqueOptions } from '../data/filter.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

const initialFilters = { search: '', stars: 'all', cuisine: 'all', arrondissement: 'all' };

export default function RestaurantsPage() {
  const { status, restaurants, error } = useRestaurants();
  const [filters, setFilters] = useState(initialFilters);

  const filteredRestaurants = useMemo(() => filterRestaurants(restaurants, filters), [restaurants, filters]);
  const cuisines = useMemo(() => uniqueOptions(restaurants, 'cuisine'), [restaurants]);
  const arrondissements = useMemo(() => uniqueOptions(restaurants, 'arrondissement'), [restaurants]);
  const starValues = useMemo(
    () => [...new Set(restaurants.map((restaurant) => restaurant.stars).filter(Boolean))].sort().map(String),
    [restaurants],
  );

  return (
    <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <StatusBlock status={status} error={error} />
      {status === 'ready' && (
        <div className="space-y-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Restaurants</h2>
              <p className="text-stone-600">
                Showing {filteredRestaurants.length} of {restaurants.length} restaurants.
              </p>
            </div>
          </div>
          <RestaurantFilters
            filters={filters}
            onChange={setFilters}
            cuisines={cuisines}
            arrondissements={arrondissements}
            starValues={starValues}
          />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredRestaurants.map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
          {filteredRestaurants.length === 0 && (
            <div className="rounded border border-stone-200 bg-white p-8 text-center shadow-panel">
              No restaurants match these filters.
            </div>
          )}
        </div>
      )}
    </section>
  );
}

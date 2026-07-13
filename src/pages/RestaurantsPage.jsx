import { useEffect, useMemo, useState } from 'react';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import RestaurantCard from '../components/RestaurantCard.jsx';
import RestaurantFilters from '../components/RestaurantFilters.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { buildCityDirectory, buildCountryDirectory } from '../data/explore.js';
import { filterRestaurants, sortRestaurants, uniqueOptions } from '../data/filter.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

const initialFilters = { search: '', cuisine: 'all', country: 'all', city: 'all' };
const PAGE_SIZE = 60;

export default function RestaurantsPage() {
  const { status, restaurants, error } = useRestaurants();
  const [filters, setFilters] = useState(initialFilters);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filteredRestaurants = useMemo(
    () => sortRestaurants(filterRestaurants(restaurants, filters)),
    [restaurants, filters],
  );
  const cuisines = useMemo(() => uniqueOptions(restaurants, 'cuisine'), [restaurants]);
  const countries = useMemo(() => buildCountryDirectory(restaurants), [restaurants]);
  const cities = useMemo(() => {
    if (filters.country === 'all') return [];
    return buildCityDirectory(restaurants.filter((restaurant) => restaurant.country_slug === filters.country));
  }, [filters.country, restaurants]);

  useEffect(() => setVisibleCount(PAGE_SIZE), [filters]);

  const updateFilters = (nextFilters) => {
    if (nextFilters.country !== filters.country) {
      setFilters({ ...nextFilters, city: 'all' });
    } else {
      setFilters(nextFilters);
    }
  };

  return (
    <section className="page-shell">
      <Breadcrumbs items={[{ label: 'World', to: '/' }, { label: 'Restaurants' }]} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && (
        <div className="space-y-6">
          <header className="max-w-3xl">
            <p className="eyebrow">Global directory</p>
            <h1 className="page-title">All restaurants</h1>
            <p className="mt-3 text-lg leading-7 text-stone-600">
              Every restaurant entity in this Wikidata snapshot is listed, including records with incomplete location data.
            </p>
          </header>
          <RestaurantFilters
            filters={filters}
            onChange={updateFilters}
            cuisines={cuisines}
            countries={countries}
            cities={cities}
          />
          <div className="flex flex-col gap-2 border-b border-stone-200 pb-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="font-medium" aria-live="polite">
              {filteredRestaurants.length.toLocaleString()} of {restaurants.length.toLocaleString()} restaurants
            </p>
            {Object.values(filters).some((value) => value !== '' && value !== 'all') && (
              <button type="button" onClick={() => setFilters(initialFilters)} className="text-left text-sm font-semibold text-michelin underline-offset-4 hover:underline">
                Clear all filters
              </button>
            )}
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredRestaurants.slice(0, visibleCount).map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
          {visibleCount < filteredRestaurants.length && (
            <div className="flex justify-center">
              <button type="button" onClick={() => setVisibleCount((count) => count + PAGE_SIZE)} className="button-secondary">
                Show more restaurants ({(filteredRestaurants.length - visibleCount).toLocaleString()} remaining)
              </button>
            </div>
          )}
          {filteredRestaurants.length === 0 && (
            <div className="rounded border border-stone-200 bg-white p-8 text-center">
              <h2 className="text-lg font-semibold">No matching restaurants</h2>
              <p className="mt-2 text-stone-600">Try removing a filter or using a broader search term.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

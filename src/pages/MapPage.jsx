import L from 'leaflet';
import { useEffect, useMemo, useRef, useState } from 'react';
import RestaurantFilters from '../components/RestaurantFilters.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { filterRestaurants, uniqueOptions } from '../data/filter.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

const initialFilters = { search: '', stars: 'all', cuisine: 'all', arrondissement: 'all' };

const redIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function RestaurantMap({ restaurants }) {
  const nodeRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!nodeRef.current || mapRef.current) {
      return;
    }

    mapRef.current = L.map(nodeRef.current, { scrollWheelZoom: true }).setView([48.8566, 2.3522], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapRef.current);
    layerRef.current = L.featureGroup().addTo(mapRef.current);
  }, []);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) {
      return;
    }

    layerRef.current.clearLayers();
    restaurants.forEach((restaurant) => {
      const stars = restaurant.stars ? `${restaurant.stars} star${restaurant.stars === 1 ? '' : 's'}` : 'Michelin starred';
      L.marker([restaurant.latitude, restaurant.longitude], { icon: redIcon })
        .bindPopup(`<strong>${restaurant.name}</strong><br>${stars}<br><a href="#/restaurants/${restaurant.id}">View details</a>`)
        .addTo(layerRef.current);
    });

    if (layerRef.current.getLayers().length > 0) {
      mapRef.current.fitBounds(layerRef.current.getBounds().pad(0.16));
    } else {
      mapRef.current.setView([48.8566, 2.3522], 5);
    }
  }, [restaurants]);

  return <div className="h-[520px] lg:h-[650px]" ref={nodeRef} aria-label="Michelin restaurants map" />;
}

export default function MapPage() {
  const { status, restaurants, error } = useRestaurants();
  const [filters, setFilters] = useState(initialFilters);
  const filteredRestaurants = useMemo(() => filterRestaurants(restaurants, filters), [restaurants, filters]);
  const mappedRestaurants = filteredRestaurants.filter((restaurant) => restaurant.latitude && restaurant.longitude);
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
          <div>
            <h2 className="text-2xl font-semibold">Map</h2>
            <p className="text-stone-600">
              {mappedRestaurants.length} restaurants with coordinates are visible on the map.
            </p>
          </div>
          <RestaurantFilters
            filters={filters}
            onChange={setFilters}
            cuisines={cuisines}
            arrondissements={arrondissements}
            starValues={starValues}
          />
          <div className="grid overflow-hidden rounded border border-stone-200 bg-white shadow-panel lg:grid-cols-[340px_1fr]">
            <aside className="max-h-[650px] overflow-auto border-b border-stone-200 p-4 lg:border-b-0 lg:border-r">
              <div className="space-y-3">
                {mappedRestaurants.map((restaurant) => (
                  <a
                    key={restaurant.id}
                    href={`#/restaurants/${restaurant.id}`}
                    className="block rounded border border-stone-200 p-3 transition hover:border-michelin hover:bg-red-50"
                  >
                    <span className="block font-semibold">{restaurant.name}</span>
                    <span className="mt-1 block text-sm text-stone-600">
                      {restaurant.stars ? `${restaurant.stars} star${restaurant.stars === 1 ? '' : 's'}` : 'Michelin starred'}
                      {restaurant.arrondissement ? ` · ${restaurant.arrondissement}` : ''}
                    </span>
                  </a>
                ))}
              </div>
            </aside>
            <RestaurantMap restaurants={mappedRestaurants} />
          </div>
        </div>
      )}
    </section>
  );
}

import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import 'leaflet/dist/leaflet.css';
import { List, Map as MapIcon, Search } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Breadcrumbs from '../components/Breadcrumbs.jsx';
import StatusBlock from '../components/StatusBlock.jsx';
import { buildCityDirectory, buildCountryDirectory } from '../data/explore.js';
import { sortRestaurants } from '../data/filter.js';
import { useRestaurants } from '../state/RestaurantContext.jsx';

const restaurantIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function textElement(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

function popupLink(label, href) {
  const link = document.createElement('a');
  link.textContent = label;
  link.href = href;
  return link;
}

function restaurantPopup(restaurant) {
  const content = document.createElement('div');
  content.append(textElement('strong', restaurant.name));
  content.append(textElement('p', 'Michelin star award recorded in Wikidata'));
  content.append(popupLink('View restaurant details', `#/restaurants/${encodeURIComponent(restaurant.id)}`));
  return content;
}

function cityPopup(city) {
  const content = document.createElement('div');
  content.append(textElement('strong', city.name));
  content.append(textElement('p', `${city.count} restaurant${city.count === 1 ? '' : 's'} in this snapshot`));
  content.append(popupLink('Show individual restaurants', `#/map?country=${encodeURIComponent(city.countrySlug)}&city=${encodeURIComponent(city.slug)}`));
  return content;
}

function cityAggregates(restaurants) {
  const groups = new Map();
  restaurants.forEach((restaurant) => {
    if (!restaurant.city_slug || restaurant.latitude === null || restaurant.longitude === null) return;
    const key = `${restaurant.country_slug}:${restaurant.city_slug}`;
    const current = groups.get(key) ?? {
      name: restaurant.city,
      slug: restaurant.city_slug,
      countrySlug: restaurant.country_slug,
      count: 0,
      latitudeTotal: 0,
      longitudeTotal: 0,
    };
    current.count += 1;
    current.latitudeTotal += restaurant.latitude;
    current.longitudeTotal += restaurant.longitude;
    groups.set(key, current);
  });
  return [...groups.values()].map((city) => ({
    ...city,
    latitude: city.latitudeTotal / city.count,
    longitude: city.longitudeTotal / city.count,
  }));
}

function RestaurantMap({ restaurants, individualMode, visible }) {
  const nodeRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!nodeRef.current || mapRef.current) return undefined;
    const map = L.map(nodeRef.current, { scrollWheelZoom: false }).setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    mapRef.current = map;
    layerRef.current = L.featureGroup().addTo(map);

    const resizeObserver = typeof ResizeObserver === 'undefined'
      ? null
      : new ResizeObserver(() => map.invalidateSize({ animate: false }));
    resizeObserver?.observe(nodeRef.current);
    return () => {
      resizeObserver?.disconnect();
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    layerRef.current.clearLayers();

    if (individualMode) {
      restaurants.forEach((restaurant) => {
        if (restaurant.latitude === null || restaurant.longitude === null) return;
        L.marker([restaurant.latitude, restaurant.longitude], { icon: restaurantIcon })
          .bindPopup(restaurantPopup(restaurant))
          .addTo(layerRef.current);
      });
    } else {
      cityAggregates(restaurants).forEach((city) => {
        const radius = Math.min(24, 8 + Math.sqrt(city.count) * 1.8);
        L.circleMarker([city.latitude, city.longitude], {
          radius,
          color: '#ffffff',
          weight: 2,
          fillColor: '#c8102e',
          fillOpacity: 0.9,
        })
          .bindPopup(cityPopup(city))
          .addTo(layerRef.current);
      });
    }

    const layers = layerRef.current.getLayers();
    if (layers.length > 0) {
      mapRef.current.fitBounds(layerRef.current.getBounds().pad(0.14), { maxZoom: individualMode ? 15 : 8 });
    } else {
      mapRef.current.setView([20, 0], 2);
    }
  }, [individualMode, restaurants]);

  useEffect(() => {
    if (!visible || !mapRef.current) return;
    const schedule = globalThis.requestAnimationFrame ?? ((callback) => globalThis.setTimeout(callback, 0));
    const cancel = globalThis.cancelAnimationFrame ?? globalThis.clearTimeout;
    const frame = schedule(() => mapRef.current?.invalidateSize({ animate: false }));
    return () => cancel(frame);
  }, [visible]);

  return <div ref={nodeRef} className="map-canvas" aria-label="Interactive map of Michelin star records" />;
}

export default function MapPage() {
  const { status, restaurants, error } = useRestaurants();
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState('map');
  const [search, setSearch] = useState('');
  const countries = useMemo(() => buildCountryDirectory(restaurants), [restaurants]);
  const requestedCountry = searchParams.get('country') ?? '';
  const country = countries.find((entry) => entry.slug === requestedCountry) ?? null;
  const countryRestaurants = country ? country.restaurants : restaurants;
  const cities = useMemo(() => buildCityDirectory(countryRestaurants), [countryRestaurants]);
  const requestedCity = searchParams.get('city') ?? '';
  const city = country ? cities.find((entry) => entry.slug === requestedCity) ?? null : null;
  const scopedRestaurants = city ? city.restaurants : countryRestaurants;
  const normalizedSearch = search.trim().toLowerCase();
  const listedRestaurants = useMemo(
    () => sortRestaurants(scopedRestaurants.filter((restaurant) =>
      !normalizedSearch || [restaurant.name, restaurant.cuisine, restaurant.address, restaurant.locality]
        .join(' ')
        .toLowerCase()
        .includes(normalizedSearch),
    )),
    [normalizedSearch, scopedRestaurants],
  );
  const mappedCount = scopedRestaurants.filter((restaurant) => restaurant.latitude !== null && restaurant.longitude !== null).length;

  const updateScope = (nextCountry, nextCity = '') => {
    const params = new URLSearchParams();
    if (nextCountry) params.set('country', nextCountry);
    if (nextCity) params.set('city', nextCity);
    setSearchParams(params);
  };

  return (
    <section className="page-shell">
      <Breadcrumbs items={[{ label: 'World', to: '/' }, { label: 'Map' }]} />
      <StatusBlock status={status} error={error} />
      {status === 'ready' && (
        <div className="space-y-5">
          <header className="max-w-3xl">
            <p className="eyebrow">Geographic explorer</p>
            <h1 className="page-title">Map the Wikidata snapshot</h1>
            <p className="mt-3 text-stone-600">
              {city ? 'Individual restaurant markers' : 'Aggregate city markers'} · {mappedCount.toLocaleString()} of {scopedRestaurants.length.toLocaleString()} scoped records have coordinates.
            </p>
          </header>

          <div className="grid gap-3 rounded border border-stone-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1.4fr]">
            <label>
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">Country</span>
              <select value={country?.slug ?? ''} onChange={(event) => updateScope(event.target.value)} className="h-11 w-full rounded border border-stone-300 px-3 text-sm">
                <option value="">World</option>
                {countries.map((entry) => <option key={entry.slug} value={entry.slug}>{entry.name} ({entry.count})</option>)}
              </select>
            </label>
            <label>
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">City</span>
              <select value={city?.slug ?? ''} disabled={!country} onChange={(event) => updateScope(country.slug, event.target.value)} className="h-11 w-full rounded border border-stone-300 px-3 text-sm disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-400">
                <option value="">{country ? 'All Wikidata cities' : 'Choose a country first'}</option>
                {cities.map((entry) => <option key={entry.slug} value={entry.slug}>{entry.name} ({entry.count})</option>)}
              </select>
            </label>
            <label className="relative">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">Filter accessible list</span>
              <Search className="pointer-events-none absolute bottom-3 left-3 text-stone-500" size={18} />
              <input value={search} onChange={(event) => setSearch(event.target.value)} className="h-11 w-full rounded border border-stone-300 pl-10 pr-3 text-sm" placeholder="Restaurant, cuisine, address…" />
            </label>
          </div>

          {(requestedCountry && !country) || (requestedCity && !city) ? (
            <p className="rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
              The requested map scope was not found. Showing the nearest valid scope instead.
            </p>
          ) : null}

          <div className="grid grid-cols-2 rounded border border-stone-300 bg-white p-1 lg:hidden" aria-label="Map display mode">
            <button type="button" aria-pressed={viewMode === 'map'} onClick={() => setViewMode('map')} className={`flex min-h-11 items-center justify-center gap-2 rounded text-sm font-semibold ${viewMode === 'map' ? 'bg-ink text-white' : 'text-stone-600'}`}><MapIcon size={18} /> Map</button>
            <button type="button" aria-pressed={viewMode === 'list'} onClick={() => setViewMode('list')} className={`flex min-h-11 items-center justify-center gap-2 rounded text-sm font-semibold ${viewMode === 'list' ? 'bg-ink text-white' : 'text-stone-600'}`}><List size={18} /> List</button>
          </div>

          <div className="overflow-hidden rounded border border-stone-200 bg-white shadow-panel lg:grid lg:grid-cols-[360px_1fr]">
            <aside className={`${viewMode === 'list' ? 'block' : 'hidden'} map-list lg:block`} aria-label="Equivalent restaurant list">
              <div className="sticky top-0 z-10 border-b border-stone-200 bg-white px-4 py-3">
                <p className="text-sm font-semibold">{listedRestaurants.length.toLocaleString()} restaurants</p>
                <p className="mt-0.5 text-xs text-stone-500">Alphabetical · includes records without coordinates</p>
              </div>
              <div className="divide-y divide-stone-100">
                {listedRestaurants.map((restaurant) => (
                  <Link key={restaurant.id} to={`/restaurants/${restaurant.id}`} className="block min-h-11 px-4 py-3 transition hover:bg-red-50 focus-visible:bg-red-50">
                    <span className="block font-semibold">{restaurant.name}</span>
                    <span className="mt-1 block text-sm text-stone-500">{restaurant.cuisine || 'Cuisine not specified'} · {restaurant.city || restaurant.locality || restaurant.country || 'Location not specified'}</span>
                  </Link>
                ))}
                {listedRestaurants.length === 0 && <p className="p-6 text-sm text-stone-600">No restaurants match this list search.</p>}
              </div>
            </aside>
            <div className={`${viewMode === 'map' ? 'block' : 'hidden'} map-wrapper lg:block`}>
              <RestaurantMap restaurants={scopedRestaurants} individualMode={Boolean(city)} visible={viewMode === 'map'} />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

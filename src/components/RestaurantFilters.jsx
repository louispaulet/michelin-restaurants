import { Search } from 'lucide-react';

export default function RestaurantFilters({ filters, onChange, cuisines, countries, cities }) {
  const update = (key) => (event) => onChange({ ...filters, [key]: event.target.value });

  return (
    <div className="rounded border border-stone-200 bg-white p-4 shadow-panel">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[1.6fr_repeat(3,1fr)]">
        <label className="relative block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">Search</span>
          <Search className="pointer-events-none absolute bottom-3 left-3 text-stone-500" size={18} />
          <input
            name="search"
            value={filters.search}
            onChange={update('search')}
            placeholder="Search restaurants, cuisine, address"
            className="h-11 w-full rounded border border-stone-300 bg-white pl-10 pr-3 text-sm outline-none focus:border-michelin focus:ring-2 focus:ring-michelin/15"
          />
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">Country</span>
          <select name="country" value={filters.country} onChange={update('country')} className="h-11 w-full rounded border border-stone-300 px-3 text-sm">
            <option value="all">All countries</option>
            {countries.map((country) => (
              <option key={country.slug} value={country.slug}>
                {country.name} ({country.count})
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">City</span>
          <select name="city" value={filters.city} onChange={update('city')} disabled={filters.country === 'all'} className="h-11 w-full rounded border border-stone-300 px-3 text-sm disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-400">
            <option value="all">{filters.country === 'all' ? 'Choose a country first' : 'All Wikidata cities'}</option>
            {cities.map((city) => (
              <option key={city.slug} value={city.slug}>
                {city.name} ({city.count})
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-stone-500">Cuisine</span>
          <select name="cuisine" value={filters.cuisine} onChange={update('cuisine')} className="h-11 w-full rounded border border-stone-300 px-3 text-sm">
            <option value="all">All cuisines</option>
            {cuisines.map((cuisine) => (
              <option key={cuisine} value={cuisine}>{cuisine}</option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}

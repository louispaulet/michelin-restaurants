import { Search } from 'lucide-react';

export default function RestaurantFilters({ filters, onChange, cuisines, arrondissements, starValues }) {
  const update = (key) => (event) => onChange({ ...filters, [key]: event.target.value });

  return (
    <div className="rounded border border-stone-200 bg-white p-4 shadow-panel">
      <div className="grid gap-3 md:grid-cols-[1.5fr_repeat(3,1fr)]">
        <label className="relative block">
          <span className="sr-only">Search</span>
          <Search className="pointer-events-none absolute left-3 top-3 text-stone-500" size={18} />
          <input
            name="search"
            value={filters.search}
            onChange={update('search')}
            placeholder="Search restaurants, cuisine, address"
            className="h-11 w-full rounded border border-stone-300 bg-white pl-10 pr-3 text-sm outline-none focus:border-michelin focus:ring-2 focus:ring-michelin/15"
          />
        </label>
        <select name="stars" value={filters.stars} onChange={update('stars')} className="h-11 rounded border border-stone-300 px-3 text-sm">
          <option value="all">All star tiers</option>
          {starValues.map((stars) => (
            <option key={stars} value={stars}>
              {stars} star{stars === '1' ? '' : 's'}
            </option>
          ))}
        </select>
        <select name="cuisine" value={filters.cuisine} onChange={update('cuisine')} className="h-11 rounded border border-stone-300 px-3 text-sm">
          <option value="all">All cuisines</option>
          {cuisines.map((cuisine) => (
            <option key={cuisine} value={cuisine}>
              {cuisine}
            </option>
          ))}
        </select>
        <select
          name="arrondissement"
          value={filters.arrondissement}
          onChange={update('arrondissement')}
          className="h-11 rounded border border-stone-300 px-3 text-sm"
        >
          <option value="all">All arrondissements</option>
          {arrondissements.map((arrondissement) => (
            <option key={arrondissement} value={arrondissement}>
              {arrondissement}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

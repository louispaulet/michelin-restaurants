import { sortRestaurants } from './filter.js';

function sortDirectoryEntries(entries) {
  return entries.sort(
    (a, b) => b.count - a.count || a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }),
  );
}

export function buildCountryDirectory(restaurants) {
  const groups = new Map();

  restaurants.forEach((restaurant) => {
    if (!restaurant.country || !restaurant.country_slug) return;
    const current = groups.get(restaurant.country_slug) ?? {
      id: restaurant.country_wikidata_id,
      name: restaurant.country,
      slug: restaurant.country_slug,
      restaurants: [],
    };
    current.restaurants.push(restaurant);
    groups.set(restaurant.country_slug, current);
  });

  return sortDirectoryEntries(
    [...groups.values()].map((country) => ({ ...country, count: country.restaurants.length })),
  );
}

export function buildCityDirectory(restaurants) {
  const groups = new Map();

  restaurants.forEach((restaurant) => {
    if (!restaurant.city || !restaurant.city_slug) return;
    const current = groups.get(restaurant.city_slug) ?? {
      id: restaurant.city_wikidata_id,
      name: restaurant.city,
      slug: restaurant.city_slug,
      restaurants: [],
    };
    current.restaurants.push(restaurant);
    groups.set(restaurant.city_slug, current);
  });

  return sortDirectoryEntries(
    [...groups.values()].map((city) => ({
      ...city,
      count: city.restaurants.length,
      restaurants: sortRestaurants(city.restaurants),
    })),
  );
}

export function findCountry(restaurants, countrySlug) {
  const country = buildCountryDirectory(restaurants).find((entry) => entry.slug === countrySlug);
  if (!country) return null;
  return {
    ...country,
    cities: buildCityDirectory(country.restaurants),
    withoutCity: sortRestaurants(country.restaurants.filter((restaurant) => !restaurant.city_slug)),
  };
}

export function findCity(restaurants, countrySlug, citySlug) {
  const country = findCountry(restaurants, countrySlug);
  if (!country) return { country: null, city: null };
  return { country, city: country.cities.find((entry) => entry.slug === citySlug) ?? null };
}

export function restaurantsWithoutCountry(restaurants) {
  return sortRestaurants(restaurants.filter((restaurant) => !restaurant.country_slug));
}

export function filterRestaurants(restaurants, filters) {
  const search = filters.search.trim().toLowerCase();
  return restaurants.filter((restaurant) => {
    const haystack = [
      restaurant.name,
      restaurant.cuisine,
      restaurant.address,
      restaurant.locality,
      restaurant.city,
      restaurant.country,
      restaurant.description,
    ]
      .join(' ')
      .toLowerCase();

    const matchesSearch = !search || haystack.includes(search);
    const matchesCuisine = filters.cuisine === 'all' || restaurant.cuisine === filters.cuisine;
    const matchesCountry = filters.country === 'all' || restaurant.country_slug === filters.country;
    const matchesCity = filters.city === 'all' || restaurant.city_slug === filters.city;

    return matchesSearch && matchesCuisine && matchesCountry && matchesCity;
  });
}

export function uniqueOptions(restaurants, key) {
  return [...new Set(restaurants.map((restaurant) => restaurant[key]).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true }),
  );
}

export function sortRestaurants(restaurants) {
  return [...restaurants].sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }),
  );
}

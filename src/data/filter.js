export function filterRestaurants(restaurants, filters) {
  const search = filters.search.trim().toLowerCase();
  return restaurants.filter((restaurant) => {
    const haystack = [
      restaurant.name,
      restaurant.cuisine,
      restaurant.address,
      restaurant.arrondissement,
      restaurant.description,
    ]
      .join(' ')
      .toLowerCase();

    const matchesSearch = !search || haystack.includes(search);
    const matchesStars = filters.stars === 'all' || String(restaurant.stars ?? '') === filters.stars;
    const matchesCuisine = filters.cuisine === 'all' || restaurant.cuisine === filters.cuisine;
    const matchesArrondissement =
      filters.arrondissement === 'all' || restaurant.arrondissement === filters.arrondissement;

    return matchesSearch && matchesStars && matchesCuisine && matchesArrondissement;
  });
}

export function uniqueOptions(restaurants, key) {
  return [...new Set(restaurants.map((restaurant) => restaurant[key]).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true }),
  );
}

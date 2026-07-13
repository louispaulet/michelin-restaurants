import { describe, expect, it } from 'vitest';
import { filterRestaurants, sortRestaurants, uniqueOptions } from './filter.js';

const restaurants = [
  { name: 'Zèbre', cuisine: 'French', address: 'Paris', city: 'Paris', country: 'France', city_slug: 'paris', country_slug: 'france' },
  { name: 'Alpha', cuisine: 'Modern', address: 'Geneva', city: 'Geneva', country: 'Switzerland', city_slug: 'geneva', country_slug: 'switzerland' },
];

describe('filterRestaurants', () => {
  it('filters worldwide records by search, cuisine, country, and city', () => {
    expect(filterRestaurants(restaurants, { search: 'paris', cuisine: 'French', country: 'france', city: 'paris' })).toHaveLength(1);
  });

  it('returns stable options and alphabetical restaurant ordering', () => {
    expect(uniqueOptions(restaurants, 'country')).toEqual(['France', 'Switzerland']);
    expect(sortRestaurants(restaurants).map((restaurant) => restaurant.name)).toEqual(['Alpha', 'Zèbre']);
  });
});

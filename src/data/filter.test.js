import { describe, expect, it } from 'vitest';
import { filterRestaurants, uniqueOptions } from './filter.js';

const restaurants = [
  { name: 'Epicure', cuisine: 'French', address: 'Paris 75008', arrondissement: '8e', stars: 3 },
  { name: 'Septime', cuisine: 'Modern', address: 'Paris 75011', arrondissement: '11e', stars: 1 },
];

describe('filterRestaurants', () => {
  it('filters by search, cuisine, arrondissement, and stars', () => {
    expect(
      filterRestaurants(restaurants, {
        search: 'epi',
        stars: '3',
        cuisine: 'French',
        arrondissement: '8e',
      }),
    ).toHaveLength(1);
  });

  it('returns stable unique options', () => {
    expect(uniqueOptions(restaurants, 'arrondissement')).toEqual(['8e', '11e']);
  });
});

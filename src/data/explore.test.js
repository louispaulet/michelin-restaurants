import { describe, expect, it } from 'vitest';
import { buildCountryDirectory, findCity, findCountry, restaurantsWithoutCountry } from './explore.js';

const restaurants = [
  { id: 'b', name: 'Beta', country: 'France', country_slug: 'france', country_wikidata_id: 'Q142', city: 'Paris', city_slug: 'paris', city_wikidata_id: 'Q90' },
  { id: 'a', name: 'Alpha', country: 'France', country_slug: 'france', country_wikidata_id: 'Q142', city: 'Paris', city_slug: 'paris', city_wikidata_id: 'Q90' },
  { id: 'c', name: 'Cityless', country: 'France', country_slug: 'france', country_wikidata_id: 'Q142', city: '', city_slug: '' },
  { id: 'd', name: 'Unknown', country: '', country_slug: '' },
];

describe('worldwide directories', () => {
  it('groups countries and cities without dropping incomplete records', () => {
    expect(buildCountryDirectory(restaurants)[0].count).toBe(3);
    expect(findCountry(restaurants, 'france').withoutCity.map((restaurant) => restaurant.id)).toEqual(['c']);
    expect(restaurantsWithoutCountry(restaurants).map((restaurant) => restaurant.id)).toEqual(['d']);
  });

  it('returns city restaurants alphabetically and rejects unknown slugs', () => {
    expect(findCity(restaurants, 'france', 'paris').city.restaurants.map((restaurant) => restaurant.name)).toEqual(['Alpha', 'Beta']);
    expect(findCity(restaurants, 'france', 'missing').city).toBeNull();
  });
});

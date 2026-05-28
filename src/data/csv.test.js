import { describe, expect, it } from 'vitest';
import { isParisFranceRestaurant, normalizeRestaurant, parseCsv } from './csv.js';

describe('parseCsv', () => {
  it('parses quoted values and normalizes coordinates', () => {
    const [restaurant] = parseCsv(
      'id,name,stars,address,latitude,longitude\none,"Table, Paris",2,"1 rue Test, Paris",48.85,2.35\n',
    ).map(normalizeRestaurant);

    expect(restaurant.name).toBe('Table, Paris');
    expect(restaurant.stars).toBe(2);
    expect(restaurant.latitude).toBe(48.85);
    expect(restaurant.longitude).toBe(2.35);
  });
});

describe('isParisFranceRestaurant', () => {
  it('keeps Paris France restaurants only', () => {
    expect(
      isParisFranceRestaurant({
        country: 'France',
        arrondissement: 'Paris - 8th Elysee, France',
        michelin_id: 'ile-de-france/paris/restaurant/epicure',
      }),
    ).toBe(true);

    expect(
      isParisFranceRestaurant({
        country: 'Switzerland',
        arrondissement: 'Geneva, Switzerland',
        michelin_id: 'geneve-region/geneve/restaurant/bayview',
      }),
    ).toBe(false);

    expect(
      isParisFranceRestaurant({
        country: 'France',
        arrondissement: 'Nice, France',
        michelin_id: 'provence-alpes-cote-dazur/nice/restaurant/test',
      }),
    ).toBe(false);
  });
});

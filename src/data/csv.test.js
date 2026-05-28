import { describe, expect, it } from 'vitest';
import { normalizeRestaurant, parseCsv } from './csv.js';

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

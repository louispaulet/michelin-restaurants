import { describe, expect, it } from 'vitest';
import { normalizeRestaurant, parseCsv } from './csv.js';

describe('parseCsv', () => {
  it('parses quoted values and normalizes coordinates', () => {
    const [restaurant] = parseCsv(
      'id,name,address,latitude,longitude\none,"Table, Paris","1 rue Test, Paris",48.85,2.35\n',
    ).map(normalizeRestaurant);

    expect(restaurant.name).toBe('Table, Paris');
    expect(restaurant.latitude).toBe(48.85);
    expect(restaurant.longitude).toBe(2.35);
  });

  it('preserves missing coordinates without inventing a location', () => {
    const [restaurant] = parseCsv('id,name,latitude,longitude\none,Unknown,,\n').map(normalizeRestaurant);
    expect(restaurant.latitude).toBeNull();
    expect(restaurant.longitude).toBeNull();
  });
});

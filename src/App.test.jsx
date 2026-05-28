import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const csv = `id,name,stars,cuisine,address,arrondissement,latitude,longitude,website,wikidata_url,michelin_id,michelin_url,description
epicure,Epicure,3,French,"112 rue du Faubourg Saint-Honoré, 75008 Paris",8e,48.872,2.314,https://example.com,https://www.wikidata.org/wiki/Q1,fr/paris/epicure,https://guide.michelin.com/fr/fr/paris-region/paris/restaurant/epicure,hotel restaurant
`;

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true, text: () => Promise.resolve(csv) })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the hash-routed restaurant list', async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText('Epicure')).toBeInTheDocument());
    expect(screen.getByText(/Showing 1 of 1 restaurants/)).toBeInTheDocument();
  });
});

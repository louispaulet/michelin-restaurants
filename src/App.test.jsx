import { render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const csv = `id,name,stars,cuisine,address,arrondissement,country,latitude,longitude,website,wikidata_url,michelin_id,michelin_url,description
epicure,Epicure,3,French,"112 rue du Faubourg Saint-Honoré, 75008 Paris",8e,France,48.872,2.314,https://example.com,https://www.wikidata.org/wiki/Q1,ile-de-france/paris/restaurant/epicure,https://guide.michelin.com/fr/fr/ile-de-france/paris/restaurant/epicure,hotel restaurant
bayview,Bayview,1,French,"Quai Wilson 47, Geneva","Geneva, Switzerland",Switzerland,46.214,6.151,https://example.com,https://www.wikidata.org/wiki/Q2,geneve-region/geneve/restaurant/bayview,https://guide.michelin.com/en/geneve-region/geneve/restaurant/bayview,not Paris
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

    const footer = screen.getByRole('contentinfo');
    expect(within(footer).getByRole('link', { name: /homepage/i })).toBeInTheDocument();
    expect(within(footer).getByRole('link', { name: /about/i })).toBeInTheDocument();
    expect(within(footer).getByRole('link', { name: /github project/i })).toHaveAttribute(
      'href',
      'https://github.com/louispaulet/michelin-restaurants',
    );
  });
});

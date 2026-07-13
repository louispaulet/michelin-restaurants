import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const csv = `id,wikidata_id,name,description,cuisine,address,locality,locality_wikidata_id,city,city_slug,city_wikidata_id,country,country_slug,country_wikidata_id,latitude,longitude,website,michelin_id,michelin_url
zeta,Q1,Zeta Table,restaurant in Paris,French,1 rue Zeta,Paris,Q90,Paris,paris,Q90,France,france,Q142,48.87,2.31,https://example.com,,
alpha,Q2,Alpha Table,,Modern,,Paris,Q90,Paris,paris,Q90,France,france,Q142,48.85,2.35,,,
cityless,Q3,Cityless Table,,,,Île-de-France,Q13917,,,,France,france,Q142,48.8,2.3,,,
bayview,Q4,Bayview,restaurant in Geneva,French,47 Quai Wilson,Geneva,Q71,Geneva,geneva,Q71,Switzerland,switzerland,Q39,46.21,6.15,,,
unknown,Q5,Unknown Place,,,,,,,,,,,,,,,,
`;

const metadata = {
  generated_at: '2026-07-13T19:46:43Z',
  counts: { restaurants: 5, countries: 2, cities: 2, mapped_restaurants: 4 },
  missing: { country: 1, city: 2, coordinates: 1, address: 3, michelin_id: 5 },
};

vi.mock('leaflet', () => {
  const map = {
    setView: vi.fn().mockReturnThis(),
    fitBounds: vi.fn(),
    invalidateSize: vi.fn(),
    remove: vi.fn(),
  };
  const layers = [];
  const group = {
    addTo: vi.fn().mockReturnThis(),
    clearLayers: vi.fn(() => { layers.length = 0; }),
    getLayers: vi.fn(() => layers),
    getBounds: vi.fn(() => ({ pad: vi.fn().mockReturnThis() })),
  };
  const marker = () => ({ bindPopup: vi.fn().mockReturnThis(), addTo: vi.fn(function addTo() { layers.push(this); return this; }) });
  return {
    default: {
      icon: vi.fn(() => ({})),
      map: vi.fn(() => map),
      tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
      featureGroup: vi.fn(() => group),
      marker: vi.fn(marker),
      circleMarker: vi.fn(marker),
    },
  };
});

describe('App', () => {
  beforeEach(() => {
    window.location.hash = '#/';
    vi.stubGlobal('ResizeObserver', class ResizeObserver { observe() {} disconnect() {} });
    vi.stubGlobal('requestAnimationFrame', (callback) => { callback(); return 1; });
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
    vi.stubGlobal('fetch', vi.fn((url) => {
      if (String(url).includes('metadata.json')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(metadata) });
      }
      return Promise.resolve({ ok: true, text: () => Promise.resolve(csv) });
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('loads the worldwide overview and filters the destination directory', async () => {
    render(<App />);
    const countryHeading = await screen.findByRole('heading', { name: /explore by country/i });
    const countrySection = within(countryHeading.closest('section'));
    expect(countrySection.getByRole('link', { name: /France/ })).toBeInTheDocument();
    expect(countrySection.getByRole('link', { name: /Switzerland/ })).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/find a country or city/i), { target: { value: 'Geneva' } });
    expect(countrySection.queryByRole('link', { name: /France/ })).not.toBeInTheDocument();
    expect(countrySection.getByRole('link', { name: /Switzerland/ })).toBeInTheDocument();
  });

  it('renders country grouping, city A–Z ordering, and unknown slugs', async () => {
    window.location.hash = '#/countries/france';
    const { unmount } = render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: 'France' })).toBeInTheDocument());
    expect(screen.getByRole('heading', { name: /city not specified in Wikidata/i })).toBeInTheDocument();
    expect(screen.getByText('Cityless Table')).toBeInTheDocument();
    unmount();

    window.location.hash = '#/countries/france/cities/paris';
    const cityView = render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: /restaurants A–Z/i })).toBeInTheDocument());
    const alpha = screen.getByText('Alpha Table');
    const zeta = screen.getByText('Zeta Table');
    expect(alpha.compareDocumentPosition(zeta) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    cityView.unmount();

    window.location.hash = '#/countries/not-real';
    render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: /country not found/i })).toBeInTheDocument());
  });

  it('provides a global directory and explicit missing values on details', async () => {
    window.location.hash = '#/restaurants';
    const { unmount } = render(<App />);
    await waitFor(() => expect(screen.getByText(/5 of 5 restaurants/i)).toBeInTheDocument());
    expect(screen.getByLabelText('Country')).toBeInTheDocument();
    unmount();

    window.location.hash = '#/restaurants/alpha';
    render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Alpha Table' })).toBeInTheDocument());
    expect(screen.getByText('Description not specified in Wikidata.')).toBeInTheDocument();
    expect(screen.getByText('Address not specified in Wikidata')).toBeInTheDocument();
  });

  it('defaults to the map on mobile and exposes an equivalent list switch', async () => {
    window.location.hash = '#/map?country=france&city=paris';
    render(<App />);
    const mapButton = await screen.findByRole('button', { name: /^map$/i });
    const listButton = screen.getByRole('button', { name: /^list$/i });
    expect(mapButton).toHaveAttribute('aria-pressed', 'true');
    expect(listButton).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(listButton);
    expect(listButton).toHaveAttribute('aria-pressed', 'true');
    expect(within(screen.getByRole('complementary', { name: /equivalent restaurant list/i })).getByText('Alpha Table')).toBeInTheDocument();
  });
});

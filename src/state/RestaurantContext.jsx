import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { normalizeRestaurant, parseCsv } from '../data/csv.js';

const RestaurantContext = createContext(null);

export function RestaurantProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', restaurants: [], metadata: null, error: null });

  useEffect(() => {
    let cancelled = false;

    const dataUrl = `${import.meta.env.BASE_URL}data/restaurants.csv?v=${__DATA_VERSION__}`;
    const metadataUrl = `${import.meta.env.BASE_URL}data/metadata.json?v=${__DATA_VERSION__}`;

    Promise.all([fetch(dataUrl), fetch(metadataUrl)])
      .then(async ([dataResponse, metadataResponse]) => {
        if (!dataResponse.ok) {
          throw new Error(`Failed to load the Wikidata snapshot: ${dataResponse.status}`);
        }
        if (!metadataResponse.ok) {
          throw new Error(`Failed to load the snapshot metadata: ${metadataResponse.status}`);
        }
        const [text, metadata] = await Promise.all([dataResponse.text(), metadataResponse.json()]);
        return { restaurants: parseCsv(text).map(normalizeRestaurant), metadata };
      })
      .then(({ restaurants, metadata }) => {
        if (!cancelled) {
          setState({ status: 'ready', restaurants, metadata, error: null });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: 'error', restaurants: [], metadata: null, error });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(() => state, [state]);

  return <RestaurantContext.Provider value={value}>{children}</RestaurantContext.Provider>;
}

export function useRestaurants() {
  const context = useContext(RestaurantContext);
  if (!context) {
    throw new Error('useRestaurants must be used inside RestaurantProvider');
  }
  return context;
}

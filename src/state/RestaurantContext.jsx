import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { isParisFranceRestaurant, normalizeRestaurant, parseCsv } from '../data/csv.js';

const RestaurantContext = createContext(null);

export function RestaurantProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', restaurants: [], error: null });

  useEffect(() => {
    let cancelled = false;

    fetch(`${import.meta.env.BASE_URL}data/restaurants.csv?v=${__DATA_VERSION__}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load dataset: ${response.status}`);
        }
        return response.text();
      })
      .then((text) => parseCsv(text).filter(isParisFranceRestaurant).map(normalizeRestaurant))
      .then((restaurants) => {
        if (!cancelled) {
          setState({ status: 'ready', restaurants, error: null });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: 'error', restaurants: [], error });
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

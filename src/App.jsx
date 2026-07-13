import { lazy, Suspense, useEffect } from 'react';
import { HashRouter, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Star } from 'lucide-react';
import AboutPage from './pages/AboutPage.jsx';
import CityPage from './pages/CityPage.jsx';
import CountryPage from './pages/CountryPage.jsx';
import HomePage from './pages/HomePage.jsx';
import RestaurantDetailPage from './pages/RestaurantDetailPage.jsx';
import RestaurantsPage from './pages/RestaurantsPage.jsx';
import { RestaurantProvider } from './state/RestaurantContext.jsx';

const MapPage = lazy(() => import('./pages/MapPage.jsx'));

const navItems = [
  { to: '/', label: 'Explore', end: true },
  { to: '/restaurants', label: 'Restaurants' },
  { to: '/map', label: 'Map' },
  { to: '/about', label: 'About' },
];

function ScrollToTop() {
  const { pathname, search } = useLocation();

  useEffect(() => {
    globalThis.scrollTo?.(0, 0);
  }, [pathname, search]);

  return null;
}

export default function App() {
  return (
    <RestaurantProvider>
      <HashRouter>
        <ScrollToTop />
        <div className="flex min-h-screen flex-col bg-paper text-ink">
          <a href="#main-content" className="skip-link">Skip to main content</a>
          <header className="sticky top-0 z-[1000] border-b border-stone-200 bg-white">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-4 py-3 sm:gap-4 sm:px-6 lg:px-8">
              <NavLink to="/" className="flex min-h-11 items-center gap-3 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-michelin" aria-label="Michelin Explorer home">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-michelin text-michelin">
                  <Star size={19} fill="currentColor" />
                </span>
                <span className="hidden sm:block">
                  <span className="font-display block text-lg font-semibold leading-5">Michelin Explorer</span>
                  <span className="block text-xs text-stone-500">Independent Wikidata directory</span>
                </span>
              </NavLink>
              <nav className="-mr-2 flex flex-1 items-center justify-end gap-0.5 py-1" aria-label="Primary navigation">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => `flex min-h-11 shrink-0 items-center rounded px-2 text-[13px] font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-michelin sm:px-3 sm:text-sm ${isActive ? 'bg-ink text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-ink'}`}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          </header>

          <main id="main-content" className="flex-1" tabIndex="-1">
            <Suspense fallback={<div className="page-shell"><div className="rounded border border-stone-200 bg-white p-6">Loading map…</div></div>}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/countries/:countrySlug" element={<CountryPage />} />
                <Route path="/countries/:countrySlug/cities/:citySlug" element={<CityPage />} />
                <Route path="/restaurants" element={<RestaurantsPage />} />
                <Route path="/restaurants/:restaurantId" element={<RestaurantDetailPage />} />
                <Route path="/map" element={<MapPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </main>

          <footer className="border-t border-stone-200 bg-white">
            <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-7 text-sm text-stone-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
              <div>
                <p className="font-display font-semibold text-ink">Michelin Explorer</p>
                <p className="mt-1 text-xs">Wikidata-only. No fallbacks.</p>
              </div>
              <nav className="flex flex-wrap items-center gap-x-5 gap-y-2" aria-label="Footer navigation">
                <NavLink to="/" className="transition hover:text-ink">World overview</NavLink>
                <NavLink to="/about" className="transition hover:text-ink">Methodology</NavLink>
                <a href="https://github.com/louispaulet/michelin-restaurants" className="transition hover:text-ink" target="_blank" rel="noreferrer">GitHub project</a>
              </nav>
            </div>
          </footer>
        </div>
      </HashRouter>
    </RestaurantProvider>
  );
}

import { HashRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { MapPinned, Search, Star } from 'lucide-react';
import AboutPage from './pages/AboutPage.jsx';
import MapPage from './pages/MapPage.jsx';
import RestaurantDetailPage from './pages/RestaurantDetailPage.jsx';
import RestaurantsPage from './pages/RestaurantsPage.jsx';
import { RestaurantProvider } from './state/RestaurantContext.jsx';

const navItems = [
  { to: '/restaurants', label: 'Restaurants' },
  { to: '/map', label: 'Map' },
  { to: '/about', label: 'About' },
];

export default function App() {
  return (
    <RestaurantProvider>
      <HashRouter>
        <div className="flex min-h-screen flex-col bg-paper text-ink">
          <header className="border-b border-stone-200 bg-white/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
              <NavLink to="/restaurants" className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded bg-michelin text-white">
                  <Star size={22} fill="currentColor" />
                </span>
                <span>
                  <span className="block text-lg font-semibold">Michelin Restaurants</span>
                  <span className="block text-sm text-stone-600">Starred tables from Wikidata</span>
                </span>
              </NavLink>
              <nav className="flex flex-wrap items-center gap-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `rounded px-3 py-2 text-sm font-medium transition ${
                        isActive ? 'bg-ink text-white' : 'text-stone-700 hover:bg-stone-100'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          </header>

          <main className="flex-1">
            <section className="border-b border-stone-200 bg-white">
              <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-michelin">Wikidata guide</p>
                  <h1 className="mt-2 max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
                    A map-first guide to Michelin-starred restaurants around the world.
                  </h1>
                </div>
                <div className="grid gap-3 self-end sm:grid-cols-2">
                  <NavLink
                    to="/restaurants"
                    className="flex items-center gap-3 rounded border border-stone-200 bg-paper px-4 py-3 font-medium shadow-panel"
                  >
                    <Search size={20} />
                    Search the list
                  </NavLink>
                  <NavLink
                    to="/map"
                    className="flex items-center gap-3 rounded bg-ink px-4 py-3 font-medium text-white shadow-panel"
                  >
                    <MapPinned size={20} />
                    Open the map
                  </NavLink>
                </div>
              </div>
            </section>

            <Routes>
              <Route path="/" element={<Navigate to="/restaurants" replace />} />
              <Route path="/restaurants" element={<RestaurantsPage />} />
              <Route path="/restaurants/:restaurantId" element={<RestaurantDetailPage />} />
              <Route path="/map" element={<MapPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="*" element={<Navigate to="/restaurants" replace />} />
            </Routes>
          </main>

          <footer className="border-t border-stone-200 bg-white">
            <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-sm text-stone-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
              <p className="font-medium text-ink">Michelin Restaurants</p>
              <nav className="flex flex-wrap items-center gap-x-5 gap-y-2" aria-label="Footer navigation">
                <NavLink to="/restaurants" className="transition hover:text-ink">
                  Homepage
                </NavLink>
                <NavLink to="/about" className="transition hover:text-ink">
                  About
                </NavLink>
                <a
                  href="https://github.com/louispaulet/michelin-restaurants"
                  className="transition hover:text-ink"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub project
                </a>
              </nav>
            </div>
          </footer>
        </div>
      </HashRouter>
    </RestaurantProvider>
  );
}

import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Breadcrumbs({ items }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-6">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-stone-600">
        {items.map((item, index) => (
          <li key={`${item.label}-${index}`} className="flex items-center gap-1">
            {index > 0 && <ChevronRight size={15} aria-hidden="true" />}
            {item.to ? (
              <Link to={item.to} className="rounded px-1 py-1 transition hover:text-michelin focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-michelin">
                {item.label}
              </Link>
            ) : (
              <span className="px-1 py-1 font-medium text-ink" aria-current="page">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

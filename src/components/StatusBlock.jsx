export default function StatusBlock({ status, error }) {
  if (status === 'loading') {
    return <div className="rounded border border-stone-200 bg-white p-6 shadow-panel">Loading restaurants...</div>;
  }

  if (status === 'error') {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-6 text-red-900 shadow-panel">
        {error?.message || 'Unable to load restaurants.'}
      </div>
    );
  }

  return null;
}

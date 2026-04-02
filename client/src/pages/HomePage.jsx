import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import ItemCard from '../components/market/ItemCard'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [trending, setTrending] = useState([])
  const [recent, setRecent] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/api/prices/trending').then(setTrending).catch(() => {})
    api.get('/api/prices/latest?limit=20').then(setRecent).catch(() => {})
  }, [])

  useEffect(() => {
    if (query.length < 2) { setResults([]); return }
    const t = setTimeout(() => {
      setSearching(true)
      api.get(`/api/items/search?q=${encodeURIComponent(query)}`)
        .then(setResults)
        .catch(() => setResults([]))
        .finally(() => setSearching(false))
    }, 300)
    return () => clearTimeout(t)
  }, [query])

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ color: '#c8a050', fontSize: '2rem', marginBottom: '0.5rem' }}>Dark & Darker Market</h1>
      <p style={{ color: '#706050', marginBottom: '2rem' }}>Track item prices over time.</p>

      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search for an item..."
        style={{ width: '100%', background: '#1a1510', border: '1px solid #3a3020', color: '#e8e0d0', padding: '0.75rem 1rem', borderRadius: 6, fontSize: '1rem', marginBottom: '1rem' }}
      />

      {query.length >= 2 && (
        <div style={{ marginBottom: '2rem' }}>
          {searching ? <LoadingSpinner /> : (
            results.length === 0
              ? <p style={{ color: '#706050' }}>No items found.</p>
              : <div style={{ display: 'grid', gap: '0.5rem' }}>
                  {results.map(item => <ItemCard key={item.id} item={item} />)}
                </div>
          )}
        </div>
      )}

      {query.length < 2 && (
        <>
          {trending.length > 0 && (
            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ color: '#a09080', fontSize: '1rem', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Most Traded Today</h2>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {trending.slice(0, 10).map(item => <ItemCard key={item.id} item={{ ...item, latest_price: item.avg_price }} />)}
              </div>
            </section>
          )}

          {recent.length > 0 && (
            <section>
              <h2 style={{ color: '#a09080', fontSize: '1rem', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recently Updated</h2>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {recent.map(item => <ItemCard key={item.id} item={{ ...item, latest_price: item.price }} />)}
              </div>
            </section>
          )}

          {trending.length === 0 && recent.length === 0 && (
            <p style={{ color: '#706050', textAlign: 'center', padding: '3rem' }}>
              No data yet. Run the scraper to start collecting market prices.
            </p>
          )}
        </>
      )}
    </div>
  )
}

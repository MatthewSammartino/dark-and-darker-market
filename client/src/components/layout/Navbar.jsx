import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { api } from '../../lib/api'

export default function Navbar() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const navigate = useNavigate()

  function handleChange(e) {
    const val = e.target.value
    setQuery(val)
    if (val.length < 2) { setResults([]); return }
    api.get(`/api/items/search?q=${encodeURIComponent(val)}`)
      .then(setResults)
      .catch(() => setResults([]))
  }

  function pick(item) {
    setQuery('')
    setResults([])
    navigate(`/item/${item.id}`)
  }

  return (
    <nav style={{ background: '#1a1510', borderBottom: '1px solid #3a3020', padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem', position: 'relative', zIndex: 100 }}>
      <Link to="/" style={{ color: '#c8a050', fontWeight: 700, fontSize: '1.1rem', textDecoration: 'none' }}>
        D&D Market
      </Link>
      <Link to="/browse" style={{ color: '#a09080', textDecoration: 'none', fontSize: '0.9rem' }}>Browse</Link>

      <div style={{ position: 'relative', marginLeft: 'auto' }}>
        <input
          value={query}
          onChange={handleChange}
          placeholder="Search items..."
          style={{ background: '#2a2010', border: '1px solid #3a3020', color: '#e8e0d0', padding: '0.4rem 0.75rem', borderRadius: 4, width: 220, fontSize: '0.9rem' }}
        />
        {results.length > 0 && (
          <div style={{ position: 'absolute', top: '100%', right: 0, background: '#1a1510', border: '1px solid #3a3020', borderRadius: 4, minWidth: 260, maxHeight: 300, overflowY: 'auto' }}>
            {results.map(item => (
              <div key={item.id} onClick={() => pick(item)} style={{ padding: '0.5rem 0.75rem', cursor: 'pointer', borderBottom: '1px solid #2a2010' }}>
                <span style={{ color: '#e8e0d0', fontSize: '0.9rem' }}>{item.name}</span>
                {item.slot && <span style={{ color: '#706050', fontSize: '0.8rem', marginLeft: '0.5rem' }}>{item.slot}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </nav>
  )
}

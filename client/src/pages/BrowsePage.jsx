import { useState } from 'react'
import { useItems } from '../hooks/useItems'
import ItemCard from '../components/market/ItemCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

const SLOTS = ['Head', 'Chest', 'Legs', 'Feet', 'Hands', 'Primary', 'Secondary', 'Ring', 'Amulet', 'Utility']
const RARITIES = ['Poor', 'Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Unique']

export default function BrowsePage() {
  const [slot, setSlot] = useState('')
  const [rarity, setRarity] = useState('')
  const [q, setQ] = useState('')

  const { items, loading, error } = useItems({ slot, q, limit: 50 })

  const filtered = rarity
    ? items.filter(i => i.latest_rarity === rarity)
    : items

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1.5rem', alignItems: 'start' }}>
      <aside>
        <h2 style={{ color: '#a09080', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>Filters</h2>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: '#706050', fontSize: '0.8rem', display: 'block', marginBottom: '0.4rem' }}>Search</label>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Name..."
            style={{ width: '100%', background: '#1a1510', border: '1px solid #2a2010', color: '#e8e0d0', padding: '0.4rem 0.5rem', borderRadius: 4, fontSize: '0.85rem' }} />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: '#706050', fontSize: '0.8rem', display: 'block', marginBottom: '0.4rem' }}>Slot</label>
          <select value={slot} onChange={e => setSlot(e.target.value)}
            style={{ width: '100%', background: '#1a1510', border: '1px solid #2a2010', color: '#e8e0d0', padding: '0.4rem', borderRadius: 4, fontSize: '0.85rem' }}>
            <option value="">All</option>
            {SLOTS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div>
          <label style={{ color: '#706050', fontSize: '0.8rem', display: 'block', marginBottom: '0.4rem' }}>Rarity</label>
          <select value={rarity} onChange={e => setRarity(e.target.value)}
            style={{ width: '100%', background: '#1a1510', border: '1px solid #2a2010', color: '#e8e0d0', padding: '0.4rem', borderRadius: 4, fontSize: '0.85rem' }}>
            <option value="">All</option>
            {RARITIES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </aside>

      <main>
        <p style={{ color: '#706050', fontSize: '0.85rem', marginBottom: '1rem' }}>{filtered.length} items</p>
        {loading ? <LoadingSpinner /> : error ? <ErrorBanner message={error.message} /> : (
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {filtered.map(item => <ItemCard key={item.id} item={item} />)}
            {filtered.length === 0 && <p style={{ color: '#706050' }}>No items found.</p>}
          </div>
        )}
      </main>
    </div>
  )
}

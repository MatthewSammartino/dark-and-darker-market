import { Link } from 'react-router-dom'
import RarityBadge from './RarityBadge'

export default function ItemCard({ item }) {
  return (
    <Link to={`/item/${item.id}`} style={{ textDecoration: 'none' }}>
      <div style={{ background: '#1a1510', border: '1px solid #2a2010', borderRadius: 6, padding: '0.75rem 1rem', cursor: 'pointer', transition: 'border-color 0.15s' }}
        onMouseEnter={e => e.currentTarget.style.borderColor = '#c8a050'}
        onMouseLeave={e => e.currentTarget.style.borderColor = '#2a2010'}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
          <span style={{ color: '#e8e0d0', fontWeight: 600, fontSize: '0.95rem' }}>{item.name}</span>
          {item.rarity && <RarityBadge rarity={item.rarity} />}
        </div>
        <div style={{ marginTop: '0.4rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: '#706050', fontSize: '0.8rem' }}>{[item.slot, item.item_type].filter(Boolean).join(' · ')}</span>
          {item.latest_price != null && (
            <span style={{ color: '#c8a050', fontWeight: 700, fontSize: '0.95rem' }}>
              {item.latest_price.toLocaleString()} g
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}

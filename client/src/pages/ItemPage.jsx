import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { usePriceHistory } from '../hooks/usePriceHistory'
import PriceChart from '../components/market/PriceChart'
import RarityBadge from '../components/market/RarityBadge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'

const RANGES = ['1d', '7d', '30d', 'all']

export default function ItemPage() {
  const { id } = useParams()
  const [item, setItem] = useState(null)
  const [itemError, setItemError] = useState(null)
  const [range, setRange] = useState('7d')
  const { data: priceData, loading: priceLoading, error: priceError } = usePriceHistory(id, range)

  useEffect(() => {
    api.get(`/api/items/${id}`)
      .then(setItem)
      .catch(setItemError)
  }, [id])

  if (itemError) return <div style={{ padding: '2rem' }}><ErrorBanner message={itemError.message} /></div>
  if (!item) return <LoadingSpinner />

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        <h1 style={{ color: '#e8e0d0', fontSize: '1.5rem' }}>{item.name}</h1>
        {item.latest_rarity && <RarityBadge rarity={item.latest_rarity} />}
      </div>
      <p style={{ color: '#706050', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        {[item.slot, item.item_type].filter(Boolean).join(' · ')}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {[
          { label: '24h Avg', value: item.price_24h_avg != null ? `${Number(item.price_24h_avg).toLocaleString()} g` : '—' },
          { label: '7d High', value: item.price_7d_high != null ? `${Number(item.price_7d_high).toLocaleString()} g` : '—' },
          { label: '7d Low',  value: item.price_7d_low  != null ? `${Number(item.price_7d_low).toLocaleString()} g`  : '—' },
          { label: '24h Vol', value: item.volume_24h ?? '0' },
        ].map(stat => (
          <div key={stat.label} style={{ background: '#1a1510', border: '1px solid #2a2010', borderRadius: 6, padding: '0.75rem', textAlign: 'center' }}>
            <div style={{ color: '#706050', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{stat.label}</div>
            <div style={{ color: '#c8a050', fontWeight: 700, fontSize: '1.1rem', marginTop: '0.25rem' }}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: '#1a1510', border: '1px solid #2a2010', borderRadius: 6, padding: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          {RANGES.map(r => (
            <button key={r} onClick={() => setRange(r)} style={{
              background: range === r ? '#c8a050' : '#2a2010',
              color: range === r ? '#0f0f0f' : '#a09080',
              border: 'none', borderRadius: 4, padding: '0.3rem 0.75rem',
              cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
            }}>
              {r.toUpperCase()}
            </button>
          ))}
        </div>
        {priceLoading ? <LoadingSpinner /> : priceError ? <ErrorBanner message={priceError.message} /> : (
          <PriceChart data={priceData?.data} />
        )}
      </div>

      {priceData?.data?.length > 0 && (
        <div style={{ background: '#1a1510', border: '1px solid #2a2010', borderRadius: 6, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: '#2a2010' }}>
                {['Time', 'Avg Price', 'Low', 'High', 'Volume'].map(h => (
                  <th key={h} style={{ padding: '0.5rem 0.75rem', textAlign: 'left', color: '#a09080', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...priceData.data].reverse().slice(0, 20).map((row, i) => (
                <tr key={i} style={{ borderTop: '1px solid #2a2010' }}>
                  <td style={{ padding: '0.4rem 0.75rem', color: '#706050' }}>
                    {new Date(row.bucket).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td style={{ padding: '0.4rem 0.75rem', color: '#c8a050', fontWeight: 600 }}>{row.avg?.toLocaleString()} g</td>
                  <td style={{ padding: '0.4rem 0.75rem', color: '#e07070' }}>{row.low?.toLocaleString()} g</td>
                  <td style={{ padding: '0.4rem 0.75rem', color: '#50c050' }}>{row.high?.toLocaleString()} g</td>
                  <td style={{ padding: '0.4rem 0.75rem', color: '#a09080' }}>{row.volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

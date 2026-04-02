import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

function formatDate(isoStr) {
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div style={{ background: '#1a1510', border: '1px solid #3a3020', padding: '0.5rem 0.75rem', borderRadius: 4, fontSize: '0.85rem' }}>
      <div style={{ color: '#a09080', marginBottom: 4 }}>{label && formatDate(label)}</div>
      <div style={{ color: '#c8a050' }}>Avg: {d?.avg?.toLocaleString()} g</div>
      <div style={{ color: '#50c050' }}>High: {d?.high?.toLocaleString()} g</div>
      <div style={{ color: '#e07070' }}>Low: {d?.low?.toLocaleString()} g</div>
      <div style={{ color: '#a09080' }}>Vol: {d?.volume}</div>
    </div>
  )
}

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: '#706050' }}>No price data yet.</div>
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2010" />
        <XAxis
          dataKey="bucket"
          tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          stroke="#706050"
          tick={{ fill: '#706050', fontSize: 11 }}
        />
        <YAxis
          stroke="#706050"
          tick={{ fill: '#706050', fontSize: 11 }}
          tickFormatter={v => `${v.toLocaleString()}g`}
          width={70}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area dataKey="high" fill="#1a2510" stroke="none" />
        <Area dataKey="low"  fill="#0f0f0f"  stroke="none" />
        <Line dataKey="avg" stroke="#c8a050" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

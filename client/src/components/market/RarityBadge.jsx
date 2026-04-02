const RARITY_COLORS = {
  Poor:       { bg: '#2a2a2a', text: '#888888', border: '#444444' },
  Common:     { bg: '#1e1e1e', text: '#cccccc', border: '#555555' },
  Uncommon:   { bg: '#0d2010', text: '#50c050', border: '#286028' },
  Rare:       { bg: '#0a1525', text: '#5090d0', border: '#204870' },
  Epic:       { bg: '#1a0a25', text: '#a050d0', border: '#502870' },
  Legendary:  { bg: '#251505', text: '#d08030', border: '#704010' },
  Unique:     { bg: '#252010', text: '#d0c030', border: '#706010' },
}

export default function RarityBadge({ rarity }) {
  const colors = RARITY_COLORS[rarity] || RARITY_COLORS.Common
  return (
    <span style={{
      background: colors.bg,
      color: colors.text,
      border: `1px solid ${colors.border}`,
      padding: '0.15rem 0.5rem',
      borderRadius: 3,
      fontSize: '0.75rem',
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {rarity || 'Unknown'}
    </span>
  )
}

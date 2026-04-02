export default function ErrorBanner({ message }) {
  return (
    <div style={{ background: '#2a0a0a', border: '1px solid #6a1010', color: '#e07070', padding: '0.75rem 1rem', borderRadius: 4, margin: '1rem 0' }}>
      {message || 'Something went wrong.'}
    </div>
  )
}

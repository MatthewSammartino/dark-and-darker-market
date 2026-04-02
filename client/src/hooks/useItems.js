import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export function useItems(params = {}) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    ).toString()
    setLoading(true)
    api.get(`/api/items${qs ? `?${qs}` : ''}`)
      .then(setItems)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [JSON.stringify(params)])

  return { items, loading, error }
}

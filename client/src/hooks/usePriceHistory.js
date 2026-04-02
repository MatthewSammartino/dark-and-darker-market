import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export function usePriceHistory(itemId, range = '7d', bucket = '6h') {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!itemId) return
    setLoading(true)
    api.get(`/api/prices/${itemId}?range=${range}&bucket=${bucket}`)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [itemId, range, bucket])

  return { data, loading, error }
}

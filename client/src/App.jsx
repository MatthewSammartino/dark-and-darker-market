import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import HomePage from './pages/HomePage'
import ItemPage from './pages/ItemPage'
import BrowsePage from './pages/BrowsePage'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#0f0f0f', color: '#e8e0d0' }}>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/item/:id" element={<ItemPage />} />
        <Route path="/browse" element={<BrowsePage />} />
      </Routes>
    </div>
  )
}

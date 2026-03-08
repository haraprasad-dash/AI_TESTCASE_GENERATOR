import { Toaster } from 'react-hot-toast'
import { HomePage } from './pages/HomePage'

function App() {
  return (
    <div className="app-container">
      <HomePage />
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#1e293b',
            borderRadius: '12px',
            padding: '16px 20px',
            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.2)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  )
}

export default App

import { ThemeProvider } from './store/ThemeContext'
import { Header } from './components/Header'
import { Dashboard } from './pages/Dashboard'

function App() {
  return (
    <ThemeProvider>
      <Header />
      <main>
        <Dashboard />
      </main>
    </ThemeProvider>
  )
}

export default App

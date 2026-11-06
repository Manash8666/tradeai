import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import axios from 'axios'
import './index.css'
import App from './App.tsx'

// Global interceptor: Reject HTML responses on API requests (e.g. Vercel SPA rewrites returning index.html)
axios.interceptors.response.use(
  (response) => {
    if (
      typeof response.data === 'string' &&
      (response.data.trim().startsWith('<!DOCTYPE') ||
        response.data.trim().startsWith('<html') ||
        response.data.includes('<title>'))
    ) {
      const error = new Error(`API route ${response.config.url} returned HTML fallback instead of JSON`);
      (error as any).response = { ...response, status: 404, data: null };
      return Promise.reject(error);
    }
    return response;
  },
  (error) => Promise.reject(error)
);

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)

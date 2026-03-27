import { motion, AnimatePresence } from 'framer-motion';
import { Moon, Sun, Zap, Shield, Activity } from 'lucide-react';
import { useTheme } from '../store/ThemeContext';

export function Header() {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      style={{
        padding: '0 var(--space-8)',
        height: '60px',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        background: isDark ? 'rgba(5,10,14,0.85)' : 'rgba(240,244,248,0.90)',
        position: 'sticky' as const,
        top: 0,
        zIndex: 50,
        transition: 'background var(--transition-slow), border-color var(--transition-slow)',
      }}
    >
      {/* LEFT: Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <motion.div
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)',
          }}
        >
          <Zap size={18} color="#000" strokeWidth={2.5} />
        </motion.div>

        <div>
          <h1 style={{
            fontSize: '1rem',
            fontWeight: 800,
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-light))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            letterSpacing: '-0.03em',
            lineHeight: 1,
          }}>
            AI Trading Platform
          </h1>
          <p style={{
            fontSize: '0.62rem',
            color: 'var(--color-text-muted)',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            marginTop: '2px',
            fontFamily: 'var(--font-mono)',
          }}>
            NSE · BSE · SEBI Compliant
          </p>
        </div>
      </div>

      {/* CENTER: Status Pills */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <span className="badge badge-success">
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--color-success)', animation: 'pulse 2s ease-in-out infinite', flexShrink: 0 }} />
          LIVE
        </span>
        <span className="badge badge-primary">
          <Shield size={9} />
          SEBI ✓
        </span>
        <span className="badge" style={{ background: 'rgba(56,189,248,0.12)', color: 'var(--color-info)', border: '1px solid rgba(56,189,248,0.25)' }}>
          <Activity size={9} />
          HFT ACTIVE
        </span>
      </div>

      {/* RIGHT: Theme toggle + profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
          v2.0.0
        </span>

        {/* Theme toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Sun size={13} style={{ color: isDark ? 'var(--color-text-disabled)' : 'var(--color-warning)', transition: 'color var(--transition-base)' }} />
          <button
            className="theme-toggle"
            data-active={(!isDark).toString()}
            onClick={toggleTheme}
            title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            aria-label="Toggle theme"
          >
            <span className="theme-toggle-knob">
              <AnimatePresence mode="wait">
                <motion.span
                  key={theme}
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ scale: 1, rotate: 0 }}
                  exit={{ scale: 0, rotate: 90 }}
                  transition={{ duration: 0.2 }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  {isDark ? <Moon size={10} /> : <Sun size={10} />}
                </motion.span>
              </AnimatePresence>
            </span>
          </button>
          <Moon size={13} style={{ color: isDark ? 'var(--color-primary)' : 'var(--color-text-disabled)', transition: 'color var(--transition-base)' }} />
        </div>

        {/* Avatar */}
        <div style={{
          width: 34,
          height: 34,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--color-primary-dark), var(--color-primary-light))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.72rem',
          fontWeight: 800,
          color: '#000',
          boxShadow: 'var(--shadow-glow)',
          flexShrink: 0,
          cursor: 'pointer',
          letterSpacing: 0,
        }}>
          TP
        </div>
      </div>
    </motion.header>
  );
}

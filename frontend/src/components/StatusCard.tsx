import { motion } from 'framer-motion';

interface StatusCardProps {
  title: string;
  value: string;
  subtitle?: string;
  status?: 'healthy' | 'warning' | 'error' | 'neutral';
  icon: string;
  delay?: number;
}

const statusColors: Record<string, string> = {
  healthy: 'var(--color-success)',
  warning: 'var(--color-warning)',
  error:   'var(--color-error)',
  neutral: 'var(--color-primary)',
};

const statusDotColors: Record<string, string> = {
  healthy: 'var(--color-success)',
  warning: 'var(--color-warning)',
  error:   'var(--color-error)',
  neutral: 'transparent',
};

export function StatusCard({ title, value, subtitle, status = 'neutral', icon, delay = 0 }: StatusCardProps) {
  const dotColor = statusDotColors[status];

  return (
    <motion.div
      className="kpi-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ scale: 1.02 }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-3)' }}>
        <span style={{ fontSize: '1.4rem', lineHeight: 1 }}>{icon}</span>
        {status !== 'neutral' && (
          <motion.span
            animate={{ opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{
              width: 8, height: 8, borderRadius: '50%',
              background: dotColor,
              boxShadow: `0 0 8px ${dotColor}`,
              flexShrink: 0,
              marginTop: 4,
            }}
          />
        )}
      </div>

      {/* Label */}
      <h3 style={{
        fontSize: '0.68rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.10em',
        color: 'var(--color-text-muted)',
        marginBottom: 'var(--space-1)',
        fontFamily: 'var(--font-sans)',
      }}>
        {title}
      </h3>

      {/* Value */}
      <p style={{
        fontSize: '1.65rem',
        fontWeight: 800,
        color: statusColors[status],
        lineHeight: 1.1,
        letterSpacing: '-0.02em',
        fontFamily: 'var(--font-mono)',
      }}>
        {value}
      </p>

      {/* Subtitle */}
      {subtitle && (
        <p style={{
          fontSize: '0.75rem',
          color: 'var(--color-text-muted)',
          marginTop: 'var(--space-1)',
          fontFamily: 'var(--font-sans)',
          lineHeight: 1.4,
        }}>
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}

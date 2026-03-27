import { motion } from 'framer-motion';
import { ShieldCheck, ShieldX } from 'lucide-react';

interface ComplianceCheck {
  name: string;
  passed: boolean;
  detail: string;
}

interface ComplianceBadgeProps {
  checks: ComplianceCheck[];
}

export function ComplianceBadge({ checks }: ComplianceBadgeProps) {
  const allPassed = checks.every(c => c.passed);

  return (
    <motion.div
      className="glass-panel"
      style={{ padding: 'var(--space-5)' }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <h3 style={{
          fontSize: '0.68rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          color: 'var(--color-text-muted)',
        }}>
          Phase 4.5 — Blockchain &amp; SEBI Compliance
        </h3>

        <motion.span
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity }}
          className={allPassed ? 'badge badge-success' : 'badge badge-error'}
        >
          {allPassed
            ? <><ShieldCheck size={9} /> COMPLIANT</>
            : <><ShieldX size={9} /> ACTION NEEDED</>}
        </motion.span>
      </div>

      {/* Check list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {checks.map((check, i) => (
          <motion.div
            key={check.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 + i * 0.08 }}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-bg-hover)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: '0.78rem' }}>{check.passed ? '✅' : '❌'}</span>
              <span style={{
                fontSize: '0.78rem',
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-sans)',
              }}>
                {check.name}
              </span>
            </div>
            <span style={{
              fontSize: '0.68rem',
              color: 'var(--color-text-muted)',
              fontFamily: 'var(--font-mono)',
            }}>
              {check.detail}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

export default function ApiNotice({ children }) {
  return (
    <div
      className="Card"
      style={{
        marginBottom: 24,
        padding: 16,
        borderLeft: '4px solid var(--color-warning, #f59e0b)',
        background: 'var(--color-surface-muted, #fffbeb)',
      }}
    >
      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>{children}</p>
    </div>
  );
}

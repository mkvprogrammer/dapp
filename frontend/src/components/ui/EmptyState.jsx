export default function EmptyState({ title, children, action, inline = false, icon: Icon }) {
  return (
    <div className={`EmptyState${inline ? ' EmptyState--inline' : ''}`}>
      {Icon && (
        <span className="EmptyState__icon" aria-hidden>
          <Icon />
        </span>
      )}
      {title && <h3 className="EmptyState__title">{title}</h3>}
      {children && <p className="EmptyState__text">{children}</p>}
      {action && <div className="EmptyState__action">{action}</div>}
    </div>
  );
}

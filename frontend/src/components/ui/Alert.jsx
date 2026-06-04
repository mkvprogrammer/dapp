export default function Alert({ variant = 'info', children, className = '' }) {
  return (
    <div className={`Alert Alert--${variant} ${className}`.trim()} role="alert">
      {children}
    </div>
  );
}

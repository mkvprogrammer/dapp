export default function LoadingBlock({ label = 'Загрузка…' }) {
  return (
    <div className="LoadingBlock" aria-busy="true">
      <span className="LoadingBlock__spinner" aria-hidden />
      <span>{label}</span>
    </div>
  );
}

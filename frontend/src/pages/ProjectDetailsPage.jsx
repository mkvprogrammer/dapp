import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import { auctionBannerFor } from '../assets/paths';
import { formatDateTime, formatTkn, projectStyle } from '../utils/format';

export default function ProjectDetailsPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [balance, setBalance] = useState(null);
  const [attendanceStats, setAttendanceStats] = useState(null);
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = Number(projectId);
    Promise.all([
      projectsApi.get(id),
      projectsApi.balance(id).catch(() => null),
      projectsApi.attendanceStats(id).catch(() => null),
      auctionsApi.list({ project_id: id, status: 'open' }),
    ])
      .then(([p, bal, stats, projectAuctions]) => {
        setProject(p);
        setBalance(bal);
        setAttendanceStats(stats);
        setAuctions(projectAuctions);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <p>Загрузка…</p>;
  if (!project) return <p>Проект не найден</p>;

  const style = projectStyle(project.id);

  return (
    <>
      <p style={{ margin: '0 0 16px', fontSize: '0.875rem' }}>
        <Link to="/projects">← Мои проекты</Link>
      </p>

      <header className="ProjectDetailsPage__hero Card">
        <div className="ProjectDetailsPage__hero-main">
          <span className={style.iconClass} style={{ fontSize: '2rem' }}>
            {style.glyph}
          </span>
          <div>
            <h1 className="PageHeader__title">{project.name}</h1>
            <p className="PageHeader__subtitle">{project.description || 'Без описания'}</p>
            <p className="ProjectDetailsPage__meta">
              Возврат при отмене: {project.refund_rate}% · Начальная эмиссия: {project.initial_supply} TKN
            </p>
            {project.join_code && (
              <p className="ProjectDetailsPage__meta">
                Код для записи: <strong>{project.join_code}</strong>
              </p>
            )}
          </div>
        </div>
        <span className={`Badge ${project.is_active ? 'Badge--success' : ''}`}>
          {project.is_active ? 'Активен' : 'Закрыт'}
        </span>
      </header>

      {balance && (
        <section className="Card" style={{ marginTop: 24 }}>
          <div className="Card__header">
            <h2 className="Card__title">Баланс в проекте</h2>
          </div>
          <div className="Card__body">
            <p>
              Доступно: <strong>{formatTkn(balance.available)}</strong> · Заморожено:{' '}
              <strong>{formatTkn(balance.frozen)}</strong>
            </p>
          </div>
        </section>
      )}

      {attendanceStats && (
        <section className="Card" style={{ marginTop: 24 }}>
          <div className="Card__header">
            <h2 className="Card__title">Посещаемость</h2>
          </div>
          <div className="Card__body">
            <p>
              Средняя посещаемость: {attendanceStats.average_attendance_percent}% · Сессий:{' '}
              {attendanceStats.total_sessions}
              {attendanceStats.my_visits != null && ` · Ваши визиты: ${attendanceStats.my_visits}`}
            </p>
          </div>
        </section>
      )}

      <section className="Card" style={{ marginTop: 24 }}>
        <div className="Card__header">
          <h2 className="Card__title">Активные аукционы</h2>
          <Link to="/auctions" className="Card__link">
            Каталог
          </Link>
        </div>
        <div className="Card__body Card__body--flush-top">
          {auctions.map((a) => (
            <article key={a.id} className="AuctionRow">
              <img className="AuctionRow__thumb" src={auctionBannerFor(a.id)} alt="" width="72" height="72" />
              <div className="AuctionRow__body">
                <h3 className="AuctionRow__title">{a.resource_name}</h3>
                <div className="AuctionRow__meta">
                  <span className="Tag">{a.status}</span>
                  <span>Мест: {a.resource_limit}</span>
                </div>
              </div>
              <Link to={`/auctions/${a.id}`} className="Btn Btn--primary Btn--sm">
                Открыть
              </Link>
            </article>
          ))}
          {auctions.length === 0 && <p>Нет аукционов в этом проекте.</p>}
        </div>
      </section>

      <section className="Card" style={{ marginTop: 24 }}>
        <div className="Card__header">
          <h2 className="Card__title">Правила проекта</h2>
        </div>
        <div className="Card__body">
          <ul>
            <li>Штрафы по расписанию: {project.penalty_schedule?.join('%, ')}%</li>
            <li>Blockchain ID: {project.blockchain_id}</li>
            <li>Создан: {formatDateTime(project.created_at)}</li>
          </ul>
        </div>
      </section>
    </>
  );
}

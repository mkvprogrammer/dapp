import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import ApiNotice from '../components/ApiNotice';
import { auctionBannerFor } from '../assets/paths';
import { formatDateTime, projectStyle } from '../utils/format';

export default function ProjectDetailsPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = Number(projectId);
    Promise.all([projectsApi.get(id), auctionsApi.list()])
      .then(([p, allAuctions]) => {
        setProject(p);
        setAuctions(allAuctions.filter((a) => a.project_id === id));
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
          </div>
        </div>
        <span className={`Badge ${project.is_active ? 'Badge--success' : ''}`}>
          {project.is_active ? 'Активен' : 'Закрыт'}
        </span>
      </header>

      <ApiNotice>
        Баланс по проекту, посещаемость и коды присутствия в API пока отсутствуют — отображаются только данные
        GET /projects/{'{id}'} и аукционы проекта.
      </ApiNotice>

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

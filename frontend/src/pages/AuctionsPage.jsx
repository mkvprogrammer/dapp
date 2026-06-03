import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import { auctionBannerFor } from '../assets/paths';

export default function AuctionsPage() {
  const [auctions, setAuctions] = useState([]);
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [projectFilter, setProjectFilter] = useState('');
  const [tab, setTab] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([auctionsApi.list(), projectsApi.list()])
      .then(([a, p]) => {
        setAuctions(a);
        setProjects(p);
      })
      .finally(() => setLoading(false));
  }, []);

  const projectMap = useMemo(() => Object.fromEntries(projects.map((p) => [p.id, p.name])), [projects]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return auctions.filter((a) => {
      if (projectFilter && String(a.project_id) !== projectFilter) return false;
      if (tab === 'active' && !['open', 'active'].includes(a.status)) return false;
      if (tab === 'closed' && a.status !== 'closed' && a.status !== 'ended') return false;
      if (q && !a.resource_name.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [auctions, search, projectFilter, tab]);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Аукционы</h1>
          <p className="PageHeader__subtitle">
            Маркетплейс учебных ресурсов: консультации, аудитории, оборудование и дополнительные занятия.
          </p>
        </div>
        <Link to="/create-auction" className="Btn Btn--primary">
          + Создать аукцион
        </Link>
      </header>

      <div className="Toolbar">
        <div className="Toolbar__search">
          <input
            type="search"
            className="Input"
            placeholder="Поиск по названию…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="AuctionsPage__filters">
        <select className="Select" value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)}>
          <option value="">Все проекты</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div className="Tabs" style={{ marginBottom: 24 }}>
        <button type="button" className={`Tabs__item${tab === 'all' ? ' Tabs__item--active' : ''}`} onClick={() => setTab('all')}>
          Все
        </button>
        <button
          type="button"
          className={`Tabs__item${tab === 'active' ? ' Tabs__item--active' : ''}`}
          onClick={() => setTab('active')}
        >
          Активные
        </button>
        <button
          type="button"
          className={`Tabs__item${tab === 'closed' ? ' Tabs__item--active' : ''}`}
          onClick={() => setTab('closed')}
        >
          Завершённые
        </button>
      </div>

      {loading && <p>Загрузка…</p>}

      <div className="AuctionsPage__layout">
        <div className="AuctionsPage__grid">
          {filtered.map((a) => (
            <Link key={a.id} to={`/auctions/${a.id}`} className="AuctionCard">
              <img className="AuctionCard__banner" src={auctionBannerFor(a.id)} alt="" />
              <div className="AuctionCard__body">
                <span className={`Badge ${a.status === 'open' || a.status === 'active' ? 'Badge--primary' : 'Badge--success'}`}>
                  {(a.status === 'open' || a.status === 'active') && <span className="LiveDot" />} {a.status}
                </span>
                <h2 className="AuctionCard__title">{a.resource_name}</h2>
                <div className="AuctionCard__meta">
                  <span className="Tag">{projectMap[a.project_id] || `Проект #${a.project_id}`}</span>
                  <span>
                    Мест: <strong>{a.resource_limit}</strong>
                  </span>
                </div>
                <div className="AuctionCard__footer">
                  <span>Проект #{a.project_id}</span>
                  <span className="Btn Btn--ghost Btn--sm">Участвовать</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}

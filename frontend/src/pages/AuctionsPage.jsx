import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import { auctionBannerFor } from '../assets/paths';
import Alert from '../components/ui/Alert';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { isOrganizerRole } from '../utils/format';

export default function AuctionsPage() {
  const { user } = useAuth();
  const [auctions, setAuctions] = useState([]);
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [projectFilter, setProjectFilter] = useState('');
  const [tab, setTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsApi.list().then(setProjects);
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    const params = { status: 'all' };
    if (projectFilter) params.project_id = Number(projectFilter);
    if (tab === 'active') params.status = 'open';
    if (tab === 'closed') params.status = 'closed';
    if (search.trim()) params.search = search.trim();
    auctionsApi
      .list(params)
      .then(setAuctions)
      .catch((err) => {
        setAuctions([]);
        setError(err.message || 'Не удалось загрузить аукционы');
      })
      .finally(() => setLoading(false));
  }, [projectFilter, tab, search]);

  const projectMap = useMemo(() => Object.fromEntries(projects.map((p) => [p.id, p.name])), [projects]);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Аукционы</h1>
          <p className="PageHeader__subtitle">
            Маркетплейс учебных ресурсов: консультации, аудитории, оборудование и доп. занятия.
          </p>
        </div>
        {isOrganizerRole(user?.role) && (
          <Link to="/create-auction" className="Btn Btn--primary">
            + Создать аукцион
          </Link>
        )}
      </header>

      <div className="FilterBar">
        <div className="FilterBar__search">
          <input
            type="search"
            className="Input"
            placeholder="Поиск по названию…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Поиск аукционов"
          />
        </div>
        <select
          className="Select FilterBar__select"
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          aria-label="Фильтр по проекту"
        >
          <option value="">Все проекты</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div className="Tabs Tabs--spaced">
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

      {loading && <LoadingBlock />}
      {error && <Alert variant="error">{error}</Alert>}

      {!loading && !error && auctions.length === 0 && (
        <EmptyState
          title={tab === 'active' ? 'Нет активных аукционов' : 'Аукционы не найдены'}
          action={
            <Link to="/projects" className="Btn Btn--secondary">
              Мои проекты
            </Link>
          }
        >
          {tab === 'active'
            ? 'Попробуйте вкладку «Все» или сбросьте фильтр проекта.'
            : 'Запишитесь на проект по коду — тогда появятся аукционы вашего курса.'}
        </EmptyState>
      )}

      {!loading && auctions.length > 0 && (
        <div className="AuctionsPage__grid">
          {auctions.map((a) => (
            <Link key={a.id} to={`/auctions/${a.id}`} className="AuctionCard LinkCard">
              <img className="AuctionCard__banner" src={auctionBannerFor(a.id)} alt="" />
              <div className="AuctionCard__body">
                <span
                  className={`Badge ${
                    a.status === 'open' || a.status === 'active' ? 'Badge--primary' : 'Badge--success'
                  }`}
                >
                  {(a.status === 'open' || a.status === 'active') && <span className="LiveDot" />}
                  {a.status === 'open' ? 'открыт' : a.status}
                </span>
                <h2 className="AuctionCard__title">{a.resource_name}</h2>
                <div className="AuctionCard__meta">
                  <span className="Tag">{projectMap[a.project_id] || `Проект #${a.project_id}`}</span>
                  <span>
                    Мест: <strong>{a.resource_limit}</strong>
                  </span>
                  {a.current_top_bid != null && (
                    <span>
                      Топ: <strong>{a.current_top_bid}</strong> TKN
                    </span>
                  )}
                </div>
                <div className="AuctionCard__footer">
                  <span className="AuctionCard__cta">Подробнее →</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}

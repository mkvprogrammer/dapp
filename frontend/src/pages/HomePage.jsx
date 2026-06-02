import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import { auctionBannerFor } from '../assets/paths';
import { useAuth } from '../context/AuthContext';
import { firstName, projectStyle } from '../utils/format';

export default function HomePage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([projectsApi.list(), auctionsApi.list()])
      .then(([p, a]) => {
        setProjects(p.filter((x) => x.is_active).slice(0, 3));
        setAuctions(a.slice(0, 3));
      })
      .finally(() => setLoading(false));
  }, []);

  const activeAuctions = auctions.filter((a) => a.status === 'open' || a.status === 'active');

  return (
    <>
      <header className="PageHeader HomePage__greeting">
        <div>
          <h1 className="PageHeader__title">Добрый день, {firstName(user?.full_name)}</h1>
          <p className="PageHeader__subtitle">
            {loading
              ? 'Загрузка…'
              : `У вас ${activeAuctions.length} активных аукционов. Уведомления — в разделе «Ещё» (API в разработке).`}
          </p>
        </div>
      </header>

      <div className="HomePage__stats">
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Проектов</p>
          <p className="HomePage__stat-value">{projects.length}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Активные аукционы</p>
          <p className="HomePage__stat-value">{activeAuctions.length}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Всего аукционов</p>
          <p className="HomePage__stat-value">{auctions.length}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Роль</p>
          <p className="HomePage__stat-value" style={{ fontSize: '1rem' }}>
            {user?.role}
          </p>
        </div>
      </div>

      <div className="DashboardGrid DashboardGrid--2col HomePage__grid">
        <div className="HomePage__main-col">
          <section className="Card">
            <div className="Card__header">
              <h2 className="Card__title">Мои проекты</h2>
              <Link to="/projects" className="Card__link">
                Все
              </Link>
            </div>
            <div className="Card__body Card__body--flush-top">
              <div className="ProjectsGrid">
                {projects.map((p) => {
                  const style = projectStyle(p.id);
                  return (
                    <Link key={p.id} to={`/projects/${p.id}`} className="ProjectCard">
                      <div className="ProjectCard__head">
                        <span className={style.iconClass}>{style.glyph}</span>
                        <div>
                          <p className="ProjectCard__name">{p.name}</p>
                          <p className="ProjectCard__meta">ID {p.id}</p>
                        </div>
                      </div>
                      <div className="ProjectCard__bar">
                        <div
                          className="ProjectCard__bar-fill"
                          style={{ width: style.barWidth, background: style.color }}
                        />
                      </div>
                    </Link>
                  );
                })}
                {!loading && projects.length === 0 && <p>Нет проектов. Запишитесь в проект на странице «Мои проекты».</p>}
              </div>
            </div>
          </section>

          <section className="Card" style={{ marginTop: 24 }}>
            <div className="Card__header">
              <h2 className="Card__title">Текущие аукционы</h2>
              <Link to="/auctions" className="Card__link">
                Каталог
              </Link>
            </div>
            <div className="Card__body Card__body--flush-top">
              {auctions.map((a) => (
                <article key={a.id} className="AuctionRow">
                  <img
                    className="AuctionRow__thumb"
                    src={auctionBannerFor(a.id)}
                    alt=""
                    width="72"
                    height="72"
                  />
                  <div className="AuctionRow__body">
                    <h3 className="AuctionRow__title">{a.resource_name}</h3>
                    <div className="AuctionRow__meta">
                      <span className="Tag">Проект #{a.project_id}</span>
                      <span>
                        <span className="LiveDot" /> {a.status}
                      </span>
                      <span>Мест: {a.resource_limit}</span>
                    </div>
                  </div>
                  <Link to={`/auctions/${a.id}`} className="Btn Btn--primary Btn--sm">
                    Участвовать
                  </Link>
                </article>
              ))}
            </div>
          </section>
        </div>

        <aside className="HomePage__sidebar">
          <section className="Card">
            <div className="Card__header">
              <h2 className="Card__title">Быстрые действия</h2>
            </div>
            <div className="Card__body HomePage__actions">
              <Link to="/create-auction" className="Btn Btn--secondary Btn--block">
                Создать аукцион
              </Link>
              <Link to="/transfers" className="Btn Btn--secondary Btn--block">
                Перевод токенов
              </Link>
              <Link to="/projects" className="Btn Btn--secondary Btn--block">
                Мои проекты
              </Link>
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}

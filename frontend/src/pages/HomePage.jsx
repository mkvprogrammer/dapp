import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../api';
import { auctionBannerFor } from '../assets/paths';
import JoinProjectForm from '../components/JoinProjectForm';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationsContext';
import { firstName, formatTkn, projectStyle } from '../utils/format';

export default function HomePage() {
  const { user } = useAuth();
  const { unreadCount } = useNotifications();
  const [dash, setDash] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDash = () => {
    setLoading(true);
    dashboardApi
      .get()
      .then(setDash)
      .catch(() => setDash(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDash();
  }, []);

  const projects = dash?.projects || [];
  const auctions = dash?.active_auctions || [];
  const activity = dash?.recent_activity || [];

  return (
    <>
      <header className="PageHeader PageHeader__row HomePage__greeting">
        <div>
          <h1 className="PageHeader__title">Добрый день, {firstName(user?.full_name)}</h1>
          <p className="PageHeader__subtitle">
            {loading
              ? 'Загрузка…'
              : `Баланс ${formatTkn(dash?.total_balance ?? 0)} · ${dash?.active_auctions_count ?? 0} активных аукционов · ${unreadCount} непрочитанных`}
          </p>
        </div>
        <Link to="/notifications" className="Btn Btn--secondary">
          Уведомления
        </Link>
      </header>

      <div className="HomePage__stats">
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Баланс TKN</p>
          <p className="HomePage__stat-value">{formatTkn(dash?.total_balance ?? 0)}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Проектов</p>
          <p className="HomePage__stat-value">{dash?.projects_count ?? 0}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Активные аукционы</p>
          <p className="HomePage__stat-value">{dash?.active_auctions_count ?? 0}</p>
        </div>
        <div className="Card HomePage__stat-card">
          <p className="HomePage__stat-label">Побед за месяц</p>
          <p className="HomePage__stat-value">{dash?.wins_this_month ?? 0}</p>
        </div>
      </div>

      {user?.role === 'student' && !loading && (dash?.projects_count ?? 0) === 0 && (
        <div className="HomePage__join">
          <JoinProjectForm onJoined={loadDash} />
        </div>
      )}

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
              {loading && <LoadingBlock />}
              {!loading && projects.length === 0 && (
                <EmptyState
                  title="Пока нет проектов"
                  action={
                    <Link to="/projects" className="Btn Btn--primary Btn--sm">
                      Записаться по коду
                    </Link>
                  }
                >
                  Вступите в проект по коду от преподавателя — на странице «Мои проекты» или в форме выше.
                </EmptyState>
              )}
              {!loading && projects.length > 0 && (
                <div className="ProjectsGrid">
                  {projects.map((p) => {
                    const style = projectStyle(p.project_id);
                    return (
                      <Link key={p.project_id} to={`/projects/${p.project_id}`} className="ProjectCard LinkCard">
                        <div className="ProjectCard__head">
                          <span className={style.iconClass}>{style.glyph}</span>
                          <div>
                            <p className="ProjectCard__name">{p.name}</p>
                            <p className="ProjectCard__meta">{formatTkn(p.token_balance)} TKN</p>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        </div>

        <section className="Card">
          <div className="Card__header">
            <h2 className="Card__title">Активные аукционы</h2>
            <Link to="/auctions" className="Card__link">
              Все
            </Link>
          </div>
          <div className="Card__body">
            {loading && <LoadingBlock />}
            {!loading && auctions.length === 0 && (
              <EmptyState
                title="Нет активных аукционов"
                action={
                  <Link to="/auctions" className="Btn Btn--secondary Btn--sm">
                    Каталог
                  </Link>
                }
              >
                Запишитесь на проект или откройте каталог аукционов.
              </EmptyState>
            )}
            {!loading && auctions.length > 0 && (
              <div className="HomePage__auction-list">
                {auctions.map((a) => (
                  <Link
                    key={a.auction_id}
                    to={`/auctions/${a.auction_id}`}
                    className="AuctionCard AuctionCard--compact LinkCard"
                  >
                    <img src={auctionBannerFor(a.auction_id)} alt="" className="AuctionCard__img" />
                    <div className="AuctionCard__body">
                      <p className="AuctionCard__title">{a.resource_name}</p>
                      <p className="AuctionCard__meta">{a.project_name}</p>
                      {a.my_bid_amount != null && (
                        <p className="AuctionCard__meta">Ваша ставка: {formatTkn(a.my_bid_amount)}</p>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>

      {activity.length > 0 && (
        <section className="Card HomePage__activity">
          <div className="Card__header">
            <h2 className="Card__title">Недавняя активность</h2>
            <Link to="/profile" className="Card__link">
              Весь профиль
            </Link>
          </div>
          <div className="Card__body">
            <ul className="ActivityList">
              {activity.map((a) => (
                <li key={a.id} className="ActivityList__item">
                  <strong>{a.title}</strong>
                  <span>{a.description}</span>
                  <time>{new Date(a.created_at).toLocaleString('ru-RU')}</time>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </>
  );
}

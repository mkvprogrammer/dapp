import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../api';
import JoinProjectForm from '../components/JoinProjectForm';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { formatTkn, isOrganizerRole, projectStyle } from '../utils/format';

export default function ProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    projectsApi
      .my()
      .then(setProjects)
      .catch(() => projectsApi.list().then(setProjects))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return projects.filter((p) => !q || p.name.toLowerCase().includes(q));
  }, [projects, search]);

  const isStudent = user?.role === 'student';

  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Мои проекты</h1>
        <p className="PageHeader__subtitle">
          {isStudent
            ? 'Запишитесь на курс по коду от преподавателя, чтобы получить TKN и участвовать в аукционах.'
            : 'Проекты, в которых вы участвуете или которые ведёте как организатор.'}
        </p>
      </header>

      {isStudent && (
        <div className="PageSection">
          <JoinProjectForm onJoined={load} />
        </div>
      )}

      {user && isOrganizerRole(user.role) && !isStudent && (
        <p className="ProjectsPage__archive-note PageSection--tight">
          Запись по коду доступна участникам с ролью <strong>student</strong>. Организатор создаёт проекты в{' '}
          <Link to="/organizer">панели организатора</Link>.
        </p>
      )}

      <div className="FilterBar">
        <div className="FilterBar__search">
          <input
            type="search"
            className="Input"
            placeholder="Поиск по названию…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Поиск проектов"
          />
        </div>
      </div>

      {loading && <LoadingBlock />}

      {!loading && filtered.length === 0 && (
        <EmptyState
          title={isStudent ? 'Вы не записаны на проекты' : 'Нет проектов'}
          action={
            isStudent ? null : (
              <Link to="/organizer" className="Btn Btn--primary">
                Панель организатора
              </Link>
            )
          }
        >
          {isStudent ? 'Введите код от преподавателя в форме выше.' : 'Создайте проект в панели организатора.'}
        </EmptyState>
      )}

      {!loading && filtered.length > 0 && (
        <div className="ProjectsPage__grid">
          {filtered.map((p) => {
            const style = projectStyle(p.id);
            return (
              <Link key={p.id} to={`/projects/${p.id}`} className="ProjectsPage__card LinkCard">
                <div className="ProjectsPage__card-head">
                  <span className={style.iconClass}>{style.glyph}</span>
                  <div className="ProjectsPage__card-info">
                    <h2 className="ProjectsPage__card-name">{p.name}</h2>
                    <div className="ProjectsPage__card-meta">
                      {p.token_balance != null ? (
                        <span>
                          Баланс: <strong>{formatTkn(p.token_balance)} TKN</strong>
                        </span>
                      ) : (
                        <span>
                          Организатор: <strong>{String(p.organizer_id).slice(0, 8)}…</strong>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div>
                  <p className="ProjectsPage__progress-label">Статус</p>
                  <div className="ProjectCard__bar">
                    <div
                      className="ProjectCard__bar-fill"
                      style={{ width: style.barWidth, background: style.color }}
                    />
                  </div>
                </div>
                <div className="ProjectsPage__card-footer">
                  <span className={`Badge ${p.is_active ? 'Badge--success' : 'Badge--muted'}`}>
                    {p.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../api';
import { ApiError } from '../api/client';
import { projectStyle } from '../utils/format';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [enrollId, setEnrollId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    projectsApi
      .list()
      .then(setProjects)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return projects.filter((p) => !q || p.name.toLowerCase().includes(q));
  }, [projects, search]);

  const handleEnroll = async () => {
    setError('');
    setMessage('');
    const id = Number(enrollId);
    if (!id) {
      setError('Укажите ID проекта');
      return;
    }
    try {
      const res = await projectsApi.enroll(id);
      setMessage(`Вы записаны в проект. Баланс: ${res.token_balance} TKN`);
      setEnrollId('');
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка записи');
    }
  };

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Мои проекты</h1>
          <p className="PageHeader__subtitle">
            Управляйте участием в учебных проектах, отслеживайте баланс токенов и активность аукционов.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="number"
            className="Input"
            placeholder="ID проекта"
            value={enrollId}
            onChange={(e) => setEnrollId(e.target.value)}
            style={{ width: 120 }}
          />
          <button type="button" className="Btn Btn--primary" onClick={handleEnroll}>
            + Присоединиться
          </button>
        </div>
      </header>

      {message && <p style={{ color: 'var(--color-success, #16a34a)' }}>{message}</p>}
      {error && <p style={{ color: 'var(--color-danger, #dc2626)' }}>{error}</p>}

      <div className="ProjectsPage__toolbar">
        <div className="ProjectsPage__toolbar-left">
          <div className="ProjectsPage__search">
            <input
              type="search"
              className="Input"
              placeholder="Поиск по названию…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="ProjectsPage__grid">
        {loading && <p>Загрузка…</p>}
        {filtered.map((p) => {
          const style = projectStyle(p.id);
          return (
            <Link key={p.id} to={`/projects/${p.id}`} className="ProjectsPage__card">
              <div className="ProjectsPage__card-head">
                <span className={style.iconClass}>{style.glyph}</span>
                <div className="ProjectsPage__card-info">
                  <h2 className="ProjectsPage__card-name">{p.name}</h2>
                  <div className="ProjectsPage__card-meta">
                    <span>
                      Организатор: <strong>{String(p.organizer_id).slice(0, 8)}…</strong>
                    </span>
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
    </>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../api';
import ApiNotice from '../components/ApiNotice';
import { useAuth } from '../context/AuthContext';

export default function OrganizerPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    projectsApi.list().then(setProjects);
  }, []);

  const myProjects =
    user?.role === 'organizer' || user?.role === 'admin'
      ? projects
      : projects.filter((p) => p.organizer_id === user?.user_id);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Панель организатора</h1>
          <p className="PageHeader__subtitle">Управление проектом, коды посещения и начисление токенов.</p>
        </div>
        {user?.role === 'admin' && (
          <Link to="/admin" className="Btn Btn--secondary">
            Админ-панель
          </Link>
        )}
      </header>

      <ApiNotice>
        Для полного макета нужны: POST /projects (создание — есть), GET /projects/{'{id}'}/members, POST
        /projects/{'{id}'}/attendance-codes, POST /projects/{'{id}'}/members/{'{user_id}'}/mint-tokens, GET
        /projects/{'{id}'}/organizer/stats.
      </ApiNotice>

      {user?.role === 'organizer' && (
        <section className="Card" style={{ marginBottom: 24 }}>
          <div className="Card__header">
            <h2 className="Card__title">Создать проект</h2>
          </div>
          <div className="Card__body">
            <CreateProjectForm onCreated={() => projectsApi.list().then(setProjects)} />
          </div>
        </section>
      )}

      <div className="OrganizerPage__actions" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        <button type="button" className="Btn Btn--secondary" disabled>
          Начислить токены
        </button>
        <button type="button" className="Btn Btn--secondary" disabled>
          Сгенерировать код посещения
        </button>
        <Link to="/create-auction" className="Btn Btn--primary">
          Создать аукцион
        </Link>
      </div>

      <section className="Card">
        <div className="Card__header">
          <h2 className="Card__title">Проекты</h2>
        </div>
        <div className="Card__body">
          <ul>
            {myProjects.map((p) => (
              <li key={p.id}>
                <Link to={`/projects/${p.id}`}>{p.name}</Link> — {p.is_active ? 'активен' : 'неактивен'}
              </li>
            ))}
          </ul>
          {myProjects.length === 0 && <p>Нет проектов для управления.</p>}
        </div>
      </section>
    </>
  );
}

function CreateProjectForm({ onCreated }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await projectsApi.create({
        name,
        description: description || null,
        password,
      });
      setName('');
      setDescription('');
      onCreated();
    } catch (err) {
      setError(err.message || 'Ошибка');
    }
  };

  return (
    <form onSubmit={submit}>
      <div className="Field Field--full">
        <label className="Field__label">Название</label>
        <input className="Input" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className="Field Field--full">
        <label className="Field__label">Описание</label>
        <input className="Input" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div className="Field Field--full">
        <label className="Field__label">Пароль кошелька</label>
        <input className="Input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
      <button type="submit" className="Btn Btn--primary" style={{ marginTop: 12 }}>
        Создать проект
      </button>
    </form>
  );
}

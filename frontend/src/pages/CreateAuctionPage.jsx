import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auctionsApi, projectsApi } from '../api';
import { ApiError } from '../api/client';
import ApiNotice from '../components/ApiNotice';
import PasswordInput from '../components/PasswordInput';

export default function CreateAuctionPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [resourceName, setResourceName] = useState('');
  const [durationHours, setDurationHours] = useState('24');
  const [lessonStart, setLessonStart] = useState('');
  const [resourceLimit, setResourceLimit] = useState('10');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    projectsApi.list().then((list) => {
      setProjects(list);
      if (list[0]) setProjectId(String(list[0].id));
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const lesson = lessonStart ? new Date(lessonStart).toISOString() : new Date().toISOString();
      const res = await auctionsApi.create({
        project_id: Number(projectId),
        resource_name: resourceName,
        duration_seconds: Number(durationHours) * 3600,
        lesson_start_time: lesson,
        resource_limit: Number(resourceLimit),
        password,
      });
      navigate(`/auctions/${res.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка создания');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Создать аукцион</h1>
        <p className="PageHeader__subtitle">Настройте параметры аукциона и опубликуйте его для участников проекта.</p>
      </header>

      <ApiNotice>
        В макете есть поля «тип ресурса», «место», «изображение», «шаг ставки», «черновик» — в API POST /auctions/ передаются
        только project_id, resource_name, duration_seconds, lesson_start_time, resource_limit и password.
      </ApiNotice>

      <div className="CreateAuctionPage__layout">
        <form className="CreateAuctionPage__form" onSubmit={handleSubmit}>
          <section className="Card CreateAuctionPage__section">
            <h2 className="CreateAuctionPage__section-title">Проект</h2>
            <div className="Field Field--full">
              <label className="Field__label" htmlFor="project">
                Проект
              </label>
              <select id="project" className="Select" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </section>

          <section className="Card CreateAuctionPage__section">
            <h2 className="CreateAuctionPage__section-title">Информация об аукционе</h2>
            <div className="CreateAuctionPage__fields">
              <div className="Field Field--full">
                <label className="Field__label" htmlFor="title">
                  Название (resource_name)
                </label>
                <input
                  id="title"
                  className="Input"
                  value={resourceName}
                  onChange={(e) => setResourceName(e.target.value)}
                  required
                  minLength={3}
                />
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="duration">
                  Длительность (часов)
                </label>
                <input
                  id="duration"
                  className="Input"
                  type="number"
                  min="1"
                  value={durationHours}
                  onChange={(e) => setDurationHours(e.target.value)}
                  required
                />
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="slots">
                  Количество мест
                </label>
                <input
                  id="slots"
                  className="Input"
                  type="number"
                  min="1"
                  value={resourceLimit}
                  onChange={(e) => setResourceLimit(e.target.value)}
                  required
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label" htmlFor="lesson">
                  Начало занятия
                </label>
                <input
                  id="lesson"
                  className="Input"
                  type="datetime-local"
                  value={lessonStart}
                  onChange={(e) => setLessonStart(e.target.value)}
                  required
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label">
                  Пароль (для подписи транзакции)
                </label>
                <PasswordInput id="create-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
            </div>
          </section>

          {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}

          <div className="CreateAuctionPage__actions">
            <button type="submit" className="Btn Btn--primary" disabled={submitting}>
              {submitting ? 'Публикация…' : 'Опубликовать'}
            </button>
            <Link to="/auctions" className="Btn Btn--secondary">
              Отмена
            </Link>
          </div>
        </form>
      </div>
    </>
  );
}

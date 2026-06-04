import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auctionsApi, projectsApi, uploadsApi } from '../api';
import { ApiError } from '../api/client';
import CreateProjectForm from '../components/CreateProjectForm';
import PasswordInput from '../components/PasswordInput';
import Alert from '../components/ui/Alert';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { isProjectOrganizer } from '../utils/format';

const RESOURCE_TYPES = [
  { value: 'consultation', label: 'Консультация' },
  { value: 'room', label: 'Аудитория' },
  { value: 'equipment', label: 'Оборудование' },
  { value: 'extra_class', label: 'Доп. занятие' },
];

export default function CreateAuctionPage() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectId, setProjectId] = useState('');
  const [resourceName, setResourceName] = useState('');
  const [resourceType, setResourceType] = useState('consultation');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [durationHours, setDurationHours] = useState('24');
  const [lessonStart, setLessonStart] = useState('');
  const [resourceLimit, setResourceLimit] = useState('10');
  const [minBid, setMinBid] = useState('1');
  const [bidStep, setBidStep] = useState('1');
  const [imageUrl, setImageUrl] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadProjects = useCallback(() => {
    if (!user || authLoading) return;
    setProjectsLoading(true);
    projectsApi
      .list()
      .then((list) => {
        const mine =
          user.role === 'admin' ? list : list.filter((p) => isProjectOrganizer(p, user));
        setProjects(mine);
        if (mine[0]) setProjectId(String(mine[0].id));
      })
      .finally(() => setProjectsLoading(false));
  }, [user, authLoading]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleImage = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      const res = await uploadsApi.image(file);
      setImageUrl(res.url);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const lesson = lessonStart ? new Date(lessonStart).toISOString() : new Date().toISOString();
      const res = await auctionsApi.create({
        project_id: Number(projectId),
        resource_name: resourceName,
        resource_type: resourceType,
        location: location || null,
        description: description || null,
        duration_seconds: Number(durationHours) * 3600,
        lesson_start_time: lesson,
        resource_limit: Number(resourceLimit),
        min_bid: Number(minBid),
        bid_step: Number(bidStep),
        image_url: imageUrl || null,
        password,
      });
      navigate(`/auctions/${res.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка создания');
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return <LoadingBlock />;
  }

  const showCreateProject = user?.role === 'organizer' && !projectsLoading && projects.length === 0;

  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Создать аукцион</h1>
        <p className="PageHeader__subtitle">Настройте параметры аукциона и опубликуйте его для участников проекта.</p>
      </header>

      {projectsLoading && <LoadingBlock />}

      {showCreateProject && (
        <section className="Card PageSection">
          <div className="Card__header">
            <h2 className="Card__title">Сначала нужен проект</h2>
          </div>
          <div className="Card__body">
            <p className="CreateAuctionPage__section-desc">
              Аукцион привязан к проекту. Создайте проект здесь — после этого появится форма аукциона.
            </p>
            <CreateProjectForm onCreated={loadProjects} />
          </div>
        </section>
      )}

      {!projectsLoading && projects.length === 0 && user?.role === 'admin' && (
        <Alert variant="info" className="PageSection--tight">
          Нет проектов в системе. Создайте проект от имени организатора или выберите существующий после появления записей.
        </Alert>
      )}

      <div className="CreateAuctionPage__layout">
        <form className="CreateAuctionPage__form" onSubmit={handleSubmit}>
          <section className="Card CreateAuctionPage__section">
            <h2 className="CreateAuctionPage__section-title">Проект</h2>
            <div className="Field Field--full">
              <label className="Field__label" htmlFor="project">
                Проект
              </label>
              <select
                id="project"
                className="Select"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                required
                disabled={!projects.length}
              >
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
                  Название
                </label>
                <input
                  id="title"
                  className="Input"
                  value={resourceName}
                  onChange={(e) => setResourceName(e.target.value)}
                  required
                  minLength={3}
                  disabled={!projects.length}
                />
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="rtype">
                  Тип ресурса
                </label>
                <select
                  id="rtype"
                  className="Select"
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value)}
                  disabled={!projects.length}
                >
                  {RESOURCE_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="location">
                  Место
                </label>
                <input
                  id="location"
                  className="Input"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={!projects.length}
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label" htmlFor="desc">
                  Описание
                </label>
                <input
                  id="desc"
                  className="Input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={!projects.length}
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label" htmlFor="image">
                  Изображение (до 2 МБ)
                </label>
                <input
                  id="image"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={handleImage}
                  disabled={!projects.length}
                />
                {imageUrl && <p className="CreateAuctionPage__section-desc">Загружено: {imageUrl}</p>}
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
                  disabled={!projects.length}
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
                  disabled={!projects.length}
                />
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="minBid">
                  Мин. ставка (TKN)
                </label>
                <input
                  id="minBid"
                  className="Input"
                  type="number"
                  min="1"
                  step="0.01"
                  value={minBid}
                  onChange={(e) => setMinBid(e.target.value)}
                  disabled={!projects.length}
                />
              </div>
              <div className="Field">
                <label className="Field__label" htmlFor="bidStep">
                  Шаг ставки (TKN)
                </label>
                <input
                  id="bidStep"
                  className="Input"
                  type="number"
                  min="1"
                  step="0.01"
                  value={bidStep}
                  onChange={(e) => setBidStep(e.target.value)}
                  disabled={!projects.length}
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
                  disabled={!projects.length}
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label">Пароль (для подписи транзакции)</label>
                <PasswordInput
                  id="create-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={!projects.length}
                />
              </div>
            </div>
          </section>

          {error && <Alert variant="error">{error}</Alert>}

          <div className="CreateAuctionPage__actions">
            <button type="submit" className="Btn Btn--primary" disabled={submitting || !projects.length}>
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

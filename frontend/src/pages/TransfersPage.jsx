import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi, transfersApi } from '../api';
import { ApiError } from '../api/client';
import PasswordInput from '../components/PasswordInput';
import Alert from '../components/ui/Alert';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { authUserId, formatTkn, isOrganizerRole, isProjectOrganizer, roleLabel } from '../utils/format';

export default function TransfersPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [history, setHistory] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [recipientId, setRecipientId] = useState('');
  const [projectId, setProjectId] = useState('');
  const [amount, setAmount] = useState('');
  const [comment, setComment] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [exporting, setExporting] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const loadProjects = useCallback(async () => {
    const enrolled = await projectsApi.my().catch(() => []);
    let list = [...enrolled];
    if (isOrganizerRole(user?.role)) {
      const all = await projectsApi.list().catch(() => []);
      const owned = all.filter((p) => isProjectOrganizer(p, user));
      const seen = new Set(list.map((p) => p.id));
      for (const p of owned) {
        if (!seen.has(p.id)) {
          list.push({ id: p.id, name: p.name, organizer_id: p.organizer_id, is_active: p.is_active, token_balance: 0 });
          seen.add(p.id);
        }
      }
    }
    setProjects(list);
    setProjectId((prev) => {
      if (!list.length) return prev;
      if (list.some((p) => String(p.id) === prev)) return prev;
      return String(list[0].id);
    });
  }, [user]);

  const load = useCallback(() => {
    loadProjects();
    setLoadingHistory(true);
    transfersApi
      .list({ direction: 'all', limit: 30 })
      .then((r) => setHistory(r.items || []))
      .finally(() => setLoadingHistory(false));
    transfersApi.recentRecipients().then((r) => setRecipients(r.items || [])).catch(() => setRecipients([]));
  }, [loadProjects]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await transfersApi.create({
        recipient_student_id: recipientId.trim(),
        project_id: Number(projectId),
        amount: Number(amount),
        comment: comment || null,
        password,
      });
      setMessage('Перевод выполнен');
      setAmount('');
      setComment('');
      setPassword('');
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка перевода');
    }
  };

  const handleExport = async () => {
    setExportting(true);
    try {
      await transfersApi.exportCsv();
    } catch (err) {
      setError(err.message || 'Ошибка выгрузки');
    } finally {
      setExportting(false);
    }
  };

  const uid = authUserId(user);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Переводы токенов</h1>
          <p className="PageHeader__subtitle">
            P2P-переводы внутри одного проекта. Участники — студенты по коду и организатор курса.
          </p>
        </div>
        <button type="button" className="Btn Btn--secondary" onClick={handleExport} disabled={exporting}>
          {exporting ? 'Выгрузка…' : 'Скачать CSV'}
        </button>
      </header>

      <div className="TransfersPage__layout">
        <section className="Card TransfersPage__form-card">
          <div className="Card__header">
            <h2 className="Card__title">Новый перевод</h2>
          </div>
          <div className="Card__body">
            {projects.length === 0 ? (
              <EmptyState title="Нет проектов" inline>
                <Link to="/projects">Вступите в проект по коду</Link> или создайте курс в панели организатора.
              </EmptyState>
            ) : (
              <>
                {recipients.length > 0 && (
                  <div className="PageSection--tight">
                    <p className="Field__label">Недавние получатели</p>
                    <div className="ChipGroup">
                      {recipients.map((r) => (
                        <button
                          key={r.student_id}
                          type="button"
                          className={`Chip${recipientId === r.student_id ? ' Chip--active' : ''}`}
                          onClick={() => setRecipientId(r.student_id)}
                        >
                          {r.full_name}
                          <span className="Chip__sub">{r.student_id}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <form className="FormStack" onSubmit={submit}>
                  <div className="Field Field--full">
                    <label className="Field__label" htmlFor="transfer-recipient">
                      ITMO ID получателя
                    </label>
                    <input
                      id="transfer-recipient"
                      className="Input"
                      value={recipientId}
                      onChange={(e) => setRecipientId(e.target.value)}
                      placeholder="Точный student_id из профиля"
                      required
                    />
                  </div>
                  <div className="Field Field--full">
                    <label className="Field__label" htmlFor="transfer-project">
                      Проект
                    </label>
                    <select
                      id="transfer-project"
                      className="Select"
                      value={projectId}
                      onChange={(e) => setProjectId(e.target.value)}
                      required
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                          {uid && String(p.organizer_id) === uid ? ' (организатор)' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="Field Field--full">
                    <label className="Field__label" htmlFor="transfer-amount">
                      Сумма (TKN)
                    </label>
                    <input
                      id="transfer-amount"
                      className="Input"
                      type="number"
                      min="1"
                      step="0.01"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      required
                    />
                  </div>
                  <div className="Field Field--full">
                    <label className="Field__label" htmlFor="transfer-comment">
                      Комментарий <span className="TransfersPage__optional">(необязательно)</span>
                    </label>
                    <input id="transfer-comment" className="Input" value={comment} onChange={(e) => setComment(e.target.value)} />
                  </div>
                  <div className="Field Field--full">
                    <label className="Field__label">Пароль аккаунта</label>
                    <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} required />
                  </div>
                  {error && <Alert variant="error">{error}</Alert>}
                  {message && <Alert variant="success">{message}</Alert>}
                  <div className="FormActions">
                    <button type="submit" className="Btn Btn--primary">
                      Перевести
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </section>

        <section className="Card">
          <div className="Card__header">
            <h2 className="Card__title">История</h2>
          </div>
          <div className="Card__body">
            {loadingHistory && <LoadingBlock />}
            {!loadingHistory && history.length === 0 && (
              <EmptyState title="Переводов пока нет" inline>
                Здесь появятся входящие и исходящие переводы.
              </EmptyState>
            )}
            {!loadingHistory && history.length > 0 && (
              <ul className="HistoryList">
                {history.map((t) => (
                  <li key={t.id} className="HistoryList__item">
                    <span className={`HistoryList__dir${t.direction === 'in' ? ' HistoryList__dir--in' : ''}`}>
                      {t.direction === 'in' ? '←' : '→'}
                    </span>
                    <div className="HistoryList__main">
                      <span className="HistoryList__name">{t.counterparty_name}</span>
                      <span className="HistoryList__meta">{t.counterparty_student_id}</span>
                      <time className="HistoryList__meta">{new Date(t.created_at).toLocaleString('ru-RU')}</time>
                    </div>
                    <span className="HistoryList__amount">{formatTkn(t.amount)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

import { useState } from 'react';
import { projectsApi } from '../api';
import { ApiError } from '../api/client';
import Alert from './ui/Alert';

/**
 * Запись студента на проект по коду (основной сценарий) или по числовому ID.
 */
export default function JoinProjectForm({ onJoined, compact = false }) {
  const [joinCode, setJoinCode] = useState('');
  const [enrollId, setEnrollId] = useState('');
  const [showId, setShowId] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleJoinByCode = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    const code = joinCode.trim();
    if (!code) {
      setError('Введите код, который выдал организатор проекта');
      return;
    }
    setBusy(true);
    try {
      const res = await projectsApi.joinByCode(code);
      setMessage(`Вы записаны в «${res.project_name}». Начислено ${res.token_balance} TKN.`);
      setJoinCode('');
      onJoined?.(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось записаться по коду');
    } finally {
      setBusy(false);
    }
  };

  const handleEnrollById = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    const id = Number(enrollId);
    if (!id) {
      setError('Укажите числовой ID проекта');
      return;
    }
    setBusy(true);
    try {
      const res = await projectsApi.enroll(id);
      setMessage(`Вы записаны в проект #${id}. Баланс: ${res.token_balance} TKN.`);
      setEnrollId('');
      onJoined?.(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка записи по ID');
    } finally {
      setBusy(false);
    }
  };

  if (compact) {
    return (
      <form className="JoinProjectForm JoinProjectForm--compact" onSubmit={handleJoinByCode}>
        <div className="JoinProjectForm__row">
          <input
            className="Input"
            placeholder="Код проекта от преподавателя"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
            autoComplete="off"
            disabled={busy}
          />
          <button type="submit" className="Btn Btn--primary" disabled={busy}>
            {busy ? 'Запись…' : 'Вступить'}
          </button>
        </div>
        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}
      </form>
    );
  }

  return (
    <section className="Card JoinProjectForm">
      <div className="Card__header">
        <h2 className="Card__title">Вступить в проект</h2>
      </div>
      <div className="Card__body">
        <p className="JoinProjectForm__hint">
          Получите код у организатора курса. После записи на кошелёк проекта начисляются стартовые TKN — ими можно
          делать ставки на аукционах.
        </p>
        <form onSubmit={handleJoinByCode}>
          <div className="Field Field--full">
            <label className="Field__label" htmlFor="join-code">
              Код проекта
            </label>
            <input
              id="join-code"
              className="Input"
              placeholder="Например, A1B2C3D4"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              autoComplete="off"
              disabled={busy}
            />
          </div>
          <button type="submit" className="Btn Btn--primary" disabled={busy}>
            {busy ? 'Запись…' : 'Записаться по коду'}
          </button>
        </form>

        <p className="JoinProjectForm__toggle">
          <button type="button" className="Btn Btn--ghost Btn--sm" onClick={() => setShowId((v) => !v)}>
            {showId ? 'Скрыть запись по ID' : 'Знаете ID проекта?'}
          </button>
        </p>

        {showId && (
          <form onSubmit={handleEnrollById}>
            <div className="Field Field--full">
              <label className="Field__label" htmlFor="enroll-id">
                ID проекта
              </label>
              <input
                id="enroll-id"
                type="number"
                min="1"
                className="Input"
                placeholder="Число из адресной строки /projects/123"
                value={enrollId}
                onChange={(e) => setEnrollId(e.target.value)}
                disabled={busy}
              />
            </div>
            <button type="submit" className="Btn Btn--secondary" disabled={busy}>
              Записаться по ID
            </button>
          </form>
        )}

        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}
      </div>
    </section>
  );
}

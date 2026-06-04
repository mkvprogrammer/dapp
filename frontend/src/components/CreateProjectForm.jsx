import { useState } from 'react';
import { projectsApi } from '../api';
import PasswordInput from './PasswordInput';
import Alert from './ui/Alert';

export default function CreateProjectForm({ onCreated }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [createdCode, setCreatedCode] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setCreatedCode('');
    try {
      const res = await projectsApi.create({
        name,
        description: description || null,
        password,
      });
      setName('');
      setDescription('');
      if (res.join_code) setCreatedCode(res.join_code);
      onCreated?.(res);
    } catch (err) {
      setError(err.message || 'Ошибка');
    }
  };

  return (
    <form className="FormStack" onSubmit={submit}>
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
        <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <Alert variant="error">{error}</Alert>}
      {createdCode && (
        <Alert variant="success">
          Проект создан. Код для записи студентов: <strong>{createdCode}</strong>
        </Alert>
      )}
      <div className="FormActions">
        <button type="submit" className="Btn Btn--primary">
          Создать проект
        </button>
      </div>
    </form>
  );
}

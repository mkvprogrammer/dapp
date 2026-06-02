import { useState } from 'react';
import { IconLock } from './icons/Icons';

const PREFIX = {
  login: 'LoginForm',
  registration: 'RegistrationForm',
};

export default function PasswordInput({
  id,
  name,
  placeholder,
  value,
  onChange,
  autoComplete = 'current-password',
  required,
  variant = 'login',
}) {
  const [visible, setVisible] = useState(false);
  const p = PREFIX[variant] || PREFIX.login;

  return (
    <div className={`${p}__input-wrap`}>
      <span className={`${p}__input-icon`} aria-hidden="true">
        <IconLock />
      </span>
      <input
        className={`${p}__input`}
        type={visible ? 'text' : 'password'}
        id={id}
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        required={required}
      />
      <button
        className={`${p}__toggle-password`}
        type="button"
        aria-label={visible ? 'Скрыть пароль' : 'Показать пароль'}
        aria-pressed={visible}
        onClick={() => setVisible((v) => !v)}
      >
        <svg
          className="icon-eye"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          hidden={visible}
        >
          <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <svg
          className="icon-eye-off"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          hidden={!visible}
        >
          <path d="M17.94 17.94A10.07 10.07 0 0112 19c-7 0-10-7-10-7a18.45 18.45 0 015.06-5.94" />
          <path d="M9.9 4.24A9.12 9.12 0 0112 5c7 0 10 7 10 7a18.5 18.5 0 01-2.16 3.19" />
          <path d="M14.12 14.12a3 3 0 01-4.24-4.24" />
          <line x1="2" y1="2" x2="22" y2="22" />
        </svg>
      </button>
    </div>
  );
}

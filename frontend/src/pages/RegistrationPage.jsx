import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../api';
import { images } from '../assets/paths';
import { ApiError } from '../api/client';
import AuthFeatureList from '../components/AuthFeatureList';
import BrandLogo from '../components/BrandLogo';
import PasswordInput from '../components/PasswordInput';
import Alert from '../components/ui/Alert';
import { IconItmoId, IconUser } from '../components/icons/Icons';

export default function RegistrationPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState('');
  const [privateKey, setPrivateKey] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (privateKey) {
    return (
      <div className="LoginPage">
        <div className="LoginPage__content LoginPage__content--narrow">
          <div className="LoginPage__card">
            <h2 className="LoginPage__card-title">Сохраните приватный ключ</h2>
            <p className="LoginPage__card-subtitle">
              Ключ кошелька показывается один раз. Сохраните его в надёжном месте — восстановление через API
              недоступно.
            </p>
            <pre className="AuthKeyBox">{privateKey}</pre>
            <button type="button" className="LoginForm__submit" onClick={() => navigate('/login')}>
              Перейти ко входу
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== password2) {
      setError('Пароли не совпадают');
      return;
    }
    setSubmitting(true);
    try {
      const res = await authApi.register({
        student_id: studentId.trim(),
        full_name: fullName.trim(),
        password,
      });
      setPrivateKey(res.private_key);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка регистрации');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="RegistrationPage">
      <div className="RegistrationPage__content">
        <aside className="RegistrationPage__aside">
          <header className="RegistrationPage__brand">
            <BrandLogo className="RegistrationPage__logo" width={56} height={56} />
            <div className="RegistrationPage__brand-text">
              <h1 className="RegistrationPage__brand-name">AuctionChain</h1>
              <p className="RegistrationPage__brand-tagline">Честное распределение ресурсов</p>
            </div>
          </header>
          <div className="RegistrationPage__intro">
            <h2 className="RegistrationPage__title">
              Добро пожаловать в <span className="RegistrationPage__title-accent">AuctionChain</span>
            </h2>
            <p className="RegistrationPage__description">
              Платформа для честного распределения ограниченных ресурсов с помощью аукционов и токенов.
            </p>
          </div>
          <div className="RegistrationPage__illustration" aria-hidden="true">
            <img
              src={images.registrationIllustration}
              alt=""
              className="RegistrationPage__illustration-img"
              width="480"
              height="360"
            />
          </div>
          <AuthFeatureList
            listClassName="RegistrationPage__features"
            itemClassName="RegistrationPage__feature"
            iconClassName="RegistrationPage__feature-icon"
          />
        </aside>

        <main className="RegistrationPage__main">
          <div className="RegistrationPage__card">
            <header className="RegistrationPage__card-header">
              <h2 className="RegistrationPage__card-title">Регистрация</h2>
              <p className="RegistrationPage__card-subtitle">Заполните форму для создания аккаунта</p>
            </header>

            {error && <Alert variant="error">{error}</Alert>}

            <form className="RegistrationForm" onSubmit={handleSubmit} noValidate>
              <div className="RegistrationForm__field">
                <label className="RegistrationForm__label" htmlFor="fullName">
                  ФИО
                </label>
                <div className="RegistrationForm__input-wrap">
                  <span className="RegistrationForm__input-icon" aria-hidden="true">
                    <IconUser />
                  </span>
                  <input
                    className="RegistrationForm__input"
                    id="fullName"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Введите ваше ФИО"
                    autoComplete="name"
                    required
                  />
                </div>
              </div>
              <div className="RegistrationForm__field">
                <label className="RegistrationForm__label" htmlFor="itmoId">
                  ITMO ID
                </label>
                <div className="RegistrationForm__input-wrap">
                  <span className="RegistrationForm__input-icon" aria-hidden="true">
                    <IconItmoId />
                  </span>
                  <input
                    className="RegistrationForm__input"
                    id="itmoId"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="Введите ваш ITMO ID"
                    autoComplete="username"
                    required
                  />
                </div>
              </div>
              <div className="RegistrationForm__field">
                <label className="RegistrationForm__label" htmlFor="password">
                  Пароль
                </label>
                <PasswordInput
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Введите пароль"
                  autoComplete="new-password"
                  required
                  variant="registration"
                />
              </div>
              <div className="RegistrationForm__field">
                <label className="RegistrationForm__label" htmlFor="password2">
                  Повторите пароль
                </label>
                <PasswordInput
                  id="password2"
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                  placeholder="Повторите пароль"
                  autoComplete="new-password"
                  required
                  variant="registration"
                />
              </div>
              <button className="RegistrationForm__submit" type="submit" disabled={submitting}>
                {submitting ? 'Регистрация…' : 'Зарегистрироваться'}
              </button>
            </form>

            <div className="RegistrationPage__divider" role="separator">
              или
            </div>

            <p className="RegistrationPage__login-prompt">
              Уже есть аккаунт?{' '}
              <Link className="RegistrationPage__login-link" to="/login">
                Войти
              </Link>
            </p>
          </div>
        </main>
      </div>
      <footer className="RegistrationPage__site-footer">
        <p>&copy; 2026 AuctionChain</p>
      </footer>
    </div>
  );
}

import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { images } from '../assets/paths';
import { ApiError } from '../api/client';
import AuthFeatureList from '../components/AuthFeatureList';
import BrandLogo from '../components/BrandLogo';
import PasswordInput from '../components/PasswordInput';
import Alert from '../components/ui/Alert';
import { IconItmoId } from '../components/icons/Icons';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [studentId, setStudentId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={location.state?.from?.pathname || '/'} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(studentId.trim(), password);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка входа');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="LoginPage">
      <div className="LoginPage__content">
        <aside className="LoginPage__aside">
          <header className="LoginPage__brand">
            <BrandLogo className="LoginPage__logo" width={56} height={56} />
            <div className="LoginPage__brand-text">
              <h1 className="LoginPage__brand-name">AuctionChain</h1>
              <p className="LoginPage__brand-tagline">Честное распределение ресурсов</p>
            </div>
          </header>
          <div className="LoginPage__intro">
            <h2 className="LoginPage__title">
              С возвращением в <span className="LoginPage__title-accent">AuctionChain</span>
            </h2>
            <p className="LoginPage__description">
              Платформа для честного распределения ограниченных ресурсов с помощью аукционов и токенов.
            </p>
          </div>
          <div className="LoginPage__illustration" aria-hidden="true">
            <img
              src={images.loginIllustration}
              alt=""
              className="LoginPage__illustration-img"
              width="480"
              height="360"
            />
          </div>
          <AuthFeatureList />
        </aside>

        <main className="LoginPage__main">
          <div className="LoginPage__card">
            <header className="LoginPage__card-header">
              <h2 className="LoginPage__card-title">Вход</h2>
              <p className="LoginPage__card-subtitle">Введите данные для входа в аккаунт</p>
            </header>

            {error && <Alert variant="error">{error}</Alert>}

            <form className="LoginForm" onSubmit={handleSubmit} noValidate>
              <div className="LoginForm__field">
                <label className="LoginForm__label" htmlFor="itmoId">
                  ITMO ID
                </label>
                <div className="LoginForm__input-wrap">
                  <span className="LoginForm__input-icon" aria-hidden="true">
                    <IconItmoId />
                  </span>
                  <input
                    className="LoginForm__input"
                    type="text"
                    id="itmoId"
                    placeholder="Введите ваш ITMO ID"
                    autoComplete="username"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="LoginForm__field">
                <label className="LoginForm__label" htmlFor="password">
                  Пароль
                </label>
                <PasswordInput
                  id="password"
                  placeholder="Введите пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  variant="login"
                />
              </div>

              <button className="LoginForm__submit" type="submit" disabled={submitting}>
                {submitting ? 'Вход…' : 'Войти'}
              </button>
            </form>

            <div className="LoginPage__divider" role="separator">
              или
            </div>

            <p className="LoginPage__register-prompt">
              Нет аккаунта?{' '}
              <Link className="LoginPage__register-link" to="/register">
                Зарегистрироваться
              </Link>
            </p>
          </div>
        </main>
      </div>
      <footer className="LoginPage__site-footer">
        <p>&copy; 2026 AuctionChain</p>
      </footer>
    </div>
  );
}

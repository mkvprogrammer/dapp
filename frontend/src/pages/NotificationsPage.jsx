import ApiNotice from '../components/ApiNotice';

const MOCK = [
  { type: 'bid', title: 'Вас перебили', body: 'Ставка на аукционе обновлена', time: '—' },
  { type: 'transfer', title: 'Входящий перевод', body: 'Ожидает API', time: '—' },
];

export default function NotificationsPage() {
  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Уведомления</h1>
          <p className="PageHeader__subtitle">События по аукционам, переводам и посещениям.</p>
        </div>
        <button type="button" className="Btn Btn--secondary" disabled>
          Отметить все прочитанными
        </button>
      </header>

      <ApiNotice>
        Нужны эндпоинты: GET /notifications, PATCH /notifications/read-all, PATCH /notifications/{'{id}'}/read с фильтрами
        по типу.
      </ApiNotice>

      <div className="NotificationsPage__list">
        {MOCK.map((n, i) => (
          <article key={i} className="NotificationCard Card">
            <h3 className="NotificationCard__title">{n.title}</h3>
            <p className="NotificationCard__body">{n.body}</p>
            <time className="NotificationCard__time">{n.time}</time>
          </article>
        ))}
      </div>
    </>
  );
}

import ApiNotice from '../components/ApiNotice';

export default function TransfersPage() {
  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Переводы токенов</h1>
        <p className="PageHeader__subtitle">P2P-переводы между участниками проекта.</p>
      </header>

      <ApiNotice>
        API для переводов отсутствует. Нужны эндпоинты: POST /transfers, GET /transfers, GET /wallet/balance,
        GET /transfers/recent-recipients, GET /transfers/export.
      </ApiNotice>

      <div className="TransfersPage__layout">
        <section className="Card TransfersPage__form-card">
          <div className="Card__header">
            <h2 className="Card__title">Новый перевод</h2>
          </div>
          <div className="Card__body">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                alert('Эндпоинт переводов ещё не реализован на backend');
              }}
            >
              <div className="Field Field--full">
                <label className="Field__label">ИСУ получателя</label>
                <input className="Input" placeholder="123456" disabled />
              </div>
              <div className="Field Field--full">
                <label className="Field__label">Сумма (TKN)</label>
                <input className="Input" type="number" disabled />
              </div>
              <div className="Field Field--full">
                <label className="Field__label">Комментарий</label>
                <input className="Input" disabled />
              </div>
              <button type="submit" className="Btn Btn--primary" disabled>
                Перевести
              </button>
            </form>
          </div>
        </section>

        <section className="Card">
          <div className="Card__header">
            <h2 className="Card__title">История переводов</h2>
          </div>
          <div className="Card__body">
            <p style={{ color: 'var(--color-text-muted)' }}>Данные появятся после реализации API.</p>
          </div>
        </section>
      </div>
    </>
  );
}

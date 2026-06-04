import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { NotificationsProvider } from './context/NotificationsContext';

import '../css/normalize.css';
import '../css/main.css';
import '../css/ui.css';
import '../css/dashboard.css';
import '../css/login.css';
import '../css/registration.css';
import '../css/home.css';
import '../css/projects.css';
import '../css/project-details.css';
import '../css/auctions.css';
import '../css/auction-details.css';
import '../css/create-auction.css';
import '../css/transfers.css';
import '../css/notifications.css';
import '../css/organizer.css';
import '../css/admin.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <NotificationsProvider>
          <App />
        </NotificationsProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);

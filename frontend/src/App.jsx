import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailsPage from './pages/ProjectDetailsPage';
import AuctionsPage from './pages/AuctionsPage';
import AuctionDetailsPage from './pages/AuctionDetailsPage';
import CreateAuctionPage from './pages/CreateAuctionPage';
import TransfersPage from './pages/TransfersPage';
import NotificationsPage from './pages/NotificationsPage';
import OrganizerPage from './pages/OrganizerPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegistrationPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:projectId" element={<ProjectDetailsPage />} />
        <Route path="auctions" element={<AuctionsPage />} />
        <Route path="auctions/:auctionId" element={<AuctionDetailsPage />} />
        <Route path="create-auction" element={<CreateAuctionPage />} />
        <Route path="transfers" element={<TransfersPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="organizer" element={<OrganizerPage />} />
      </Route>

      <Route
        path="admin"
        element={
          <ProtectedRoute roles={['admin']}>
            <AppLayout pageClass="AdminPage" />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

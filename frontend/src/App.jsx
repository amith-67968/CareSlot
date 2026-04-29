import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import Landing from './pages/Landing';
import AuthPage from './pages/AuthPage';
import DashboardLayout from './layouts/DashboardLayout';
import Overview from './pages/dashboard/Overview';
import Chat from './pages/dashboard/Chat';
import SkinAnalysis from './pages/dashboard/SkinAnalysis';
import PCODAssessment from './pages/dashboard/PCODAssessment';
import Appointments from './pages/dashboard/Appointments';
import Doctors from './pages/dashboard/Doctors';
import Profile from './pages/dashboard/Profile';
import Notifications from './pages/dashboard/Notifications';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/auth" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Overview />} />
        <Route path="chat" element={<Chat />} />
        <Route path="skin" element={<SkinAnalysis />} />
        <Route path="pcod" element={<PCODAssessment />} />
        <Route path="appointments" element={<Appointments />} />
        <Route path="doctors" element={<Doctors />} />
        <Route path="profile" element={<Profile />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;

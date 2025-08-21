import { Provider } from 'react-redux';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { Layout } from './components/common/Layout';
import { Toaster } from './components/common/Toaster';
import { ContactsPage } from './pages/Contacts/ContactsPage';
import { DashboardPage } from './pages/Dashboard/DashboardPage';
import { store } from './store';

// Import chart configuration to register Chart.js components
import './utils/chartConfig';

const CampaignsPage = () => (
  <div className="animate-fade-in">
    <h2 className="text-2xl font-bold text-gray-900">Campaigns</h2>
    <p className="text-gray-600 mt-2">Campaign management coming soon</p>
  </div>
);

const ValidationPage = () => (
  <div className="animate-fade-in">
    <h2 className="text-2xl font-bold text-gray-900">Validation</h2>
    <p className="text-gray-600 mt-2">Multi-platform validation coming soon</p>
  </div>
);

const AnalyticsPage = () => (
  <div className="animate-fade-in">
    <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
    <p className="text-gray-600 mt-2">Advanced analytics coming soon</p>
  </div>
);

const ReportsPage = () => (
  <div className="animate-fade-in">
    <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
    <p className="text-gray-600 mt-2">Reporting system coming soon</p>
  </div>
);

function App() {
  return (
    <Provider store={store}>
      <ErrorBoundary>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/contacts" element={<ContactsPage />} />
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/validation" element={<ValidationPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
            </Routes>
          </Layout>
          <Toaster />
        </Router>
      </ErrorBoundary>
    </Provider>
  );
}

export default App;

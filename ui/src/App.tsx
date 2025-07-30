import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import './force-light.css';
import ControlDashboard from './ControlDashboard';
import ControlTimeline from './ControlTimeline';
import ControlRegistry from './ControlRegistry';
import ControlDetail from './ControlDetail';
import ComparisonView from './ComparisonView';
import ConfigurationPanel from './ConfigurationPanel';
import ComplianceReports from './ComplianceReports';
import DataInspector from './DataInspector';
import EvidenceReports from './components/EvidenceReports';
import ControlScripts from './components/ControlScripts';

// Create an Apollo Client instance
const client = new ApolloClient({
  uri: 'http://localhost:8002/graphql',
  cache: new InMemoryCache()
});

function App() {
  return (
    <ApolloProvider client={client}>
      <Router>
        <div className="App">
          <nav className="App-nav">
            <div className="nav-brand">
              <span className="brand-icon">⚡</span>
              <span className="brand-name">Control-UX</span>
              <span className="brand-subtitle">Banking Control Monitoring Platform</span>
            </div>
            <ul className="nav-menu">
              <li><Link to="/" className="nav-link">Comparison</Link></li>
              <li><Link to="/dashboard" className="nav-link">Dashboard</Link></li>
              <li><Link to="/timeline" className="nav-link">Timeline</Link></li>
              <li><Link to="/registry" className="nav-link">Registry</Link></li>
              <li><Link to="/configuration" className="nav-link">Configuration</Link></li>
              <li><Link to="/reports" className="nav-link">Reports</Link></li>
              <li><Link to="/evidence-reports" className="nav-link">Evidence</Link></li>
              <li><Link to="/control-scripts" className="nav-link">Scripts</Link></li>
              <li><Link to="/data-inspector" className="nav-link">Inspector</Link></li>
            </ul>
            <div className="nav-status">
              <span className="status-indicator"></span>
              <span className="status-text">Live</span>
            </div>
          </nav>
          <main className="App-main">
            <Routes>
              <Route path="/" element={<ComparisonView />} />
              <Route path="/dashboard" element={<ControlDashboard />} />
              <Route path="/timeline" element={<ControlTimeline />} />
              <Route path="/registry" element={<ControlRegistry />} />
              <Route path="/control/:controlId" element={<ControlDetail />} />
              <Route path="/configuration" element={<ConfigurationPanel />} />
              <Route path="/reports" element={<ComplianceReports />} />
              <Route path="/evidence-reports" element={<EvidenceReports />} />
              <Route path="/control-scripts" element={<ControlScripts />} />
              <Route path="/data-inspector" element={<DataInspector />} />
            </Routes>
          </main>
          <footer className="App-footer">
            <div className="footer-info">
              <span>Control-UX v1.0</span>
              <span className="separator">|</span>
              <span>Last sync: <span id="last-sync">--:--:--</span></span>
              <span className="separator">|</span>
              <span>Controls monitored: <span id="control-count">0</span></span>
            </div>
          </footer>
        </div>
      </Router>
    </ApolloProvider>
  );
}

export default App;
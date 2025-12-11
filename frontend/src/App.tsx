import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { ApplicationForm } from './pages/ApplicationForm';
import { ApplicationResults } from './pages/ApplicationResults';
import { LenderPolicies } from './pages/LenderPolicies';
import { Applications } from './pages/Applications';
import './index.css';

function App() {
  return (
    <BrowserRouter basename="/kaaj">
      <div className="app">
        <nav className="navbar">
          <div className="container navbar-content">
            <div className="navbar-brand">
              <span>Lender Matching</span> Platform
            </div>
            <ul className="navbar-nav">
              <li>
                <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  New Application
                </NavLink>
              </li>
              <li>
                <NavLink to="/applications" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  Applications
                </NavLink>
              </li>
              <li>
                <NavLink to="/lenders" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                  Lender Policies
                </NavLink>
              </li>
            </ul>
          </div>
        </nav>

        <main className="page">
          <div className="container">
            <Routes>
              <Route path="/" element={<ApplicationForm />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/applications/:id/results" element={<ApplicationResults />} />
              <Route path="/lenders" element={<LenderPolicies />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Home from '../pages/Home';
import UploadRequest from '../pages/UploadRequest';
import Dashboard from '../pages/Dashboard';
import Simulation from '../pages/Simulation';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/upload-request" element={<UploadRequest />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/simulacion" element={<Simulation />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
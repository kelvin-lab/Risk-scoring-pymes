import { NavLink } from 'react-router-dom';
import { Home, Upload, BarChart2, Sliders } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r flex flex-col">
      <div className="p-6 text-2xl font-bold text-blue-600">ALFATECH</div>
      <nav className="flex-1 px-4 py-2">
        <NavLink to="/" className={({ isActive }) => `flex items-center px-4 py-2 mt-2 text-gray-700 rounded-md hover:bg-gray-200 ${isActive ? 'bg-gray-200' : ''}`}>
          <Home className="w-5 h-5" />
          <span className="mx-4">Inicio</span>
        </NavLink>
        <NavLink to="/evaluacion" className={({ isActive }) => `flex items-center px-4 py-2 mt-2 text-gray-700 rounded-md hover:bg-gray-200 ${isActive ? 'bg-gray-200' : ''}`}>
          <Upload className="w-5 h-5" />
          <span className="mx-4">Nueva Evaluación</span>
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => `flex items-center px-4 py-2 mt-2 text-gray-700 rounded-md hover:bg-gray-200 ${isActive ? 'bg-gray-200' : ''}`}>
          <BarChart2 className="w-5 h-5" />
          <span className="mx-4">Dashboard</span>
        </NavLink>
        <NavLink to="/simulacion" className={({ isActive }) => `flex items-center px-4 py-2 mt-2 text-gray-700 rounded-md hover:bg-gray-200 ${isActive ? 'bg-gray-200' : ''}`}>
          <Sliders className="w-5 h-5" />
          <span className="mx-4">Simulación</span>
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;
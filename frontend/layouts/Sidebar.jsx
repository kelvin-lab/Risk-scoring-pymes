import { NavLink } from 'react-router-dom';
import { FaHome, FaFileUpload, FaChartBar, FaSlidersH } from 'react-icons/fa';

const Sidebar = () => {

  const linkClasses = "flex items-center px-4 py-3 mt-2 text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white transition-colors duration-200";
  const activeLinkClasses = "bg-blue-600 text-white";

  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      <div className="p-6 text-2xl font-bold text-white text-center border-b border-gray-700">
        ALFATECH
      </div>
      <nav className="flex-1 px-4 py-4">
        <NavLink to="/" className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}>
          <FaHome className="w-5 h-5" />
          <span className="mx-4 font-medium">Home</span>
        </NavLink>
        <NavLink to="/upload-request" className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}>
          <FaFileUpload className="w-5 h-5" />
          <span className="mx-4 font-medium">Nueva evaluación</span>
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}>
          <FaChartBar className="w-5 h-5" />
          <span className="mx-4 font-medium">Dashboard</span>
        </NavLink>
        <NavLink to="/simulacion" className={({ isActive }) => `${linkClasses} ${isActive ? activeLinkClasses : ''}`}>
          <FaSlidersH className="w-5 h-5" />
          <span className="mx-4 font-medium">Simulación</span>
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;
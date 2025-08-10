import { useLocation } from 'react-router-dom';

const routeTitles = {
  '/': 'Home',
  '/upload-request': 'Nueva evaluación de riesgo',
  '/dashboard': 'Dashboard de riesgo',
  '/simulacion': 'Simulador de escenarios'
};

const Navbar = () => {
  const location = useLocation();
  const title = routeTitles[location.pathname] || 'AlfaTech';

  return (
    <header className="flex justify-start items-center p-3 bg-gray-800 border-b border-gray-700">
      <h1 className="text-xl text-white font-semibold ml-4">{title}</h1>
    </header>
  );
};

export default Navbar;
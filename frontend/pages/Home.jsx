import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">Plataforma de Evaluación de Riesgo PYME</h1>
      <p className="text-lg text-gray-600 mb-8">Utilizamos IA y datos no tradicionales para un análisis financiero preciso y rápido.</p>
      <Link to="/evaluacion">
        <button className="bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 transition duration-300">
          Iniciar Evaluación
        </button>
      </Link>
    </div>
  );
};

export default Home;
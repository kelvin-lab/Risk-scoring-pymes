import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getScoringResult } from '../services/scoringAPI';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import NoDataPopup from '../components/NoDataPopup';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const Dashboard = () => {
  const [scoringData, setScoringData] = useState(null);
  const [companyName, setCompanyName] = useState('');
  const [noData, setNoData] = useState(false);

  useEffect(() => {
    const dataString = sessionStorage.getItem('scoringResult');
    const name = sessionStorage.getItem('companyName');
    if (name) {
      setCompanyName(name);
    }

    if (dataString) {
      const rawData = JSON.parse(dataString);
      if (rawData.decision) { // This is the real data from backend
        sessionStorage.setItem('initialStatistics', JSON.stringify(rawData.decision.estadisticas));

        const transformedData = {
          riskScore: rawData.decision.nivel_riesgo,
          creditSuggested: rawData.decision.credito_sugerido.monto,
          factors: rawData.decision.factores_clave_riesgo.top_5[0],
          riskFactors: Object.keys(rawData.decision.estadisticas).map(key => ({
            subject: key.charAt(0).toUpperCase() + key.slice(1),
            A: rawData.decision.estadisticas[key].value,
            fullMark: rawData.decision.estadisticas[key].max,
          })),
          summary: `${rawData.decision.resumen.parrafo_1}\n\n${rawData.decision.resumen.parrafo_2}`
        };
        setScoringData(transformedData);
      } else { // This is mock data or already transformed data
        setScoringData(rawData);
      }
    } else { // No data in session storage
      setNoData(true);
    }
  }, []);

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'bajo':
        return 'bg-green-500 text-green-100';
      case 'medio':
        return 'bg-orange-500 text-orange-100';
      case 'alto':
        return 'bg-red-500 text-red-100';
      default:
        return 'bg-gray-500 text-gray-100';
    }
  };

  const radarChartData = {
    labels: scoringData?.riskFactors.map(f => f.subject) || [],
    datasets: [
      {
        label: companyName,
        data: scoringData?.riskFactors.map(f => f.A) || [],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      }
    ],
  };

  const radarChartOptions = {
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        pointLabels: {
          color: '#E5E7EB',
          font: {
            size: 12,
          }
        },
        ticks: {
          color: '#9CA3AF',
          backdropColor: 'transparent',
        },
        max: scoringData ? Math.max(...scoringData.riskFactors.map(f => f.fullMark)) : 150,
      },
    },
    plugins: {
      legend: {
        labels: {
          color: '#E5E7EB',
        },
      },
    },
  };

  if (noData) {
    return <NoDataPopup message="No se han cargado datos para el análisis. Por favor, sube un archivo para comenzar." to="/upload-request" buttonText="Ir a Nueva evaluación" />;
  }

  if (!scoringData) {
    return <div className="text-center text-white">Cargando datos del dashboard...</div>;
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen p-8">
      {/* Top Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2">
          <h1 className="text-4xl font-bold">{companyName}</h1>
          <p className="text-xl text-gray-400">Recomendación de crédito y análisis</p>
        </div>
        <div className="flex items-center justify-end space-x-4">
          <div className={`px-4 py-2 rounded-lg font-bold text-lg ${getRiskColor(scoringData.riskScore)}`}>
            Riesgo: {scoringData.riskScore}
          </div>
          <Link to="/simulacion">
            <button className="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-300">
              Simular escenario
            </button>
          </Link>
        </div>
      </div>

      {/* Central Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Financial Report */}
        <div className="lg:col-span-1 bg-gray-800 p-6 rounded-xl shadow-lg space-y-4">
            <h2 className="text-2xl font-bold text-blue-400 border-b border-gray-700 pb-2">Informe del análisis financiero</h2>
            <div>
                <h3 className="text-lg font-semibold text-gray-300">Crédito sugerido</h3>
                <p className="text-3xl font-bold text-green-400">${scoringData.creditSuggested.toLocaleString()}</p>
            </div>
            <div>
                <h3 className="text-lg font-semibold text-gray-300">Factores clave de riesgo</h3>
                <ul className="list-disc list-inside text-gray-400 space-y-1 mt-2">
                    {scoringData.factors.map((factor, index) => (
                        <li key={index} className="capitalize">{factor}</li>
                    ))}
                </ul>
            </div>
             <div>
                <h3 className="text-lg font-semibold text-gray-300">Resumen del perfil</h3>
                <p className="text-gray-400 mt-1 text-justify whitespace-pre-line">{scoringData.summary}</p>
            </div>
        </div>

        {/* Right Column: Radar Chart */}
        <div className="lg:col-span-2 bg-gray-800 p-6 rounded-xl shadow-lg">
          <h2 className="text-2xl font-bold text-blue-400 mb-4">Análisis comparativo de factores</h2>
          <div style={{ position: 'relative', height: '60vh' }}>
            <Radar data={radarChartData} options={radarChartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
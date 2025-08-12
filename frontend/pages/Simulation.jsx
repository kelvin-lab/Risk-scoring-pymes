import { useState, useEffect } from 'react';
import { getScoringResult, getSimulationResult } from '../services/scoringAPI';
import { Radar } from 'react-chartjs-2';
import { FaInfoCircle } from 'react-icons/fa';
import NoDataPopup from '../components/NoDataPopup';

// Re-importing ChartJS elements for the radar chart
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-center border-b border-gray-700 pb-3 mb-4">
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">&times;</button>
        </div>
        <div>{children}</div>
        <div className="text-right mt-5">
            <button onClick={onClose} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Cerrar</button>
        </div>
      </div>
    </div>
  );
};

const SimulationSlider = ({ label, value, onChange, min, max, step, unit }) => (
    <div className="flex-1">
        <label className="block text-sm font-medium text-gray-300">{label}</label>
        <input 
            type="range" 
            min={min} 
            max={max} 
            step={step}
            value={value} 
            onChange={onChange} 
            className="w-full h-2 bg-gray-700 rounded-lg cursor-pointer"
        />
        <span className="text-blue-400 font-bold">{value}{unit}</span>
    </div>
);

const Simulation = () => {
  const [initialData, setInitialData] = useState(null);
  const [isModalOpen, setModalOpen] = useState(false);
  const [simulatedValues, setSimulatedValues] = useState({ ingresos: 50, reputacion: 75, pago: 90 });
  const [predictionData, setPredictionData] = useState(null);
  const [currentRisk, setCurrentRisk] = useState('Medio');
  const [simulationHistory, setSimulationHistory] = useState([]);
  const [simulationCount, setSimulationCount] = useState(0);
  const [companyName, setCompanyName] = useState('');
  const [noData, setNoData] = useState(false);

  const historyColors = [
    { backgroundColor: 'rgba(255, 99, 132, 0.2)', borderColor: 'rgba(255, 99, 132, 1)' },
    { backgroundColor: 'rgba(75, 192, 192, 0.2)', borderColor: 'rgba(75, 192, 192, 1)' },
    { backgroundColor: 'rgba(255, 205, 86, 0.2)', borderColor: 'rgba(255, 205, 86, 1)' },
  ];

  useEffect(() => {
    const statsString = sessionStorage.getItem('initialStatistics');
    const name = sessionStorage.getItem('companyName');
    if (name) {
      setCompanyName(name);
    }
    
    if (statsString) {
      const initialStats = JSON.parse(statsString);
      
      const riskFactors = Object.keys(initialStats).map(key => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1),
        A: initialStats[key].value,
        fullMark: initialStats[key].max,
      }));

      const data = {
          riskFactors: riskFactors,
      };

      setInitialData(data);
      setPredictionData({
          labels: data.riskFactors.map(f => f.subject),
          datasets: [
              {
                  label: 'Predicción Actual',
                  data: data.riskFactors.map(f => f.A),
                  backgroundColor: 'rgba(54, 162, 235, 0.2)',
                  borderColor: 'rgba(54, 162, 235, 1)',
                  borderWidth: 2,
              }
          ]
      });
    } else {
      setNoData(true);
    }
  }, []);

  const handleSliderChange = (key, value) => {
    setSimulatedValues(prev => ({ ...prev, [key]: Number(value) }));
  };

  const handlePrediction = async () => {
    try {
      const result = await getSimulationResult(simulatedValues);
      const { estadisticas, nivel_riesgo } = result;

      const newCount = simulationCount + 1;
      setSimulationCount(newCount);
      setCurrentRisk(nivel_riesgo);

      const newChartData = initialData.riskFactors.map(factor => {
        const key = factor.subject.toLowerCase().replace(/\s/g, '');
        if (estadisticas[key]) {
          return estadisticas[key].value;
        }
        return factor.A; // Keep old value if not in simulation response
      });

      const newHistoryEntry = {
        data: newChartData,
        label: `Simulación ${newCount}`,
      };

      const updatedHistory = [newHistoryEntry, ...simulationHistory].slice(0, 3);
      setSimulationHistory(updatedHistory);

      const historyDatasets = updatedHistory.map((entry, index) => ({
        ...entry,
        backgroundColor: historyColors[index].backgroundColor,
        borderColor: historyColors[index].borderColor,
        borderWidth: 2,
      }));

      setPredictionData(prevData => ({
        ...prevData,
        datasets: [prevData.datasets[0], ...historyDatasets],
      }));

    } catch (error) {
      console.error("Failed to get simulation:", error);
      // Here you could set an error state and display a message to the user
    }
  };

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'bajo': return 'bg-green-500 text-green-100';
      case 'medio': return 'bg-orange-500 text-orange-100';
      case 'alto': return 'bg-red-500 text-red-100';
      default: return 'bg-gray-500 text-gray-100';
    }
  };

  const radarChartOptions = {
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
        grid: { color: 'rgba(255, 255, 255, 0.2)' },
        pointLabels: { color: '#E5E7EB', font: { size: 12 } },
        ticks: { color: '#9CA3AF', backdropColor: 'transparent' },
      },
    },
    plugins: {
      legend: { labels: { color: '#E5E7EB' } },
    },
  };

  if (noData) {
    return <NoDataPopup message="No se han cargado datos para simulación. Por favor, sube un archivo para comenzar." to="/upload-request" buttonText="Ir a Nueva evaluación" />;
  }

  if (!initialData || !predictionData) {
    return <div className="text-center text-white">Cargando datos de simulación...</div>;
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen p-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2">
          <h1 className="text-4xl font-bold">{companyName || "<Empresa>"} </h1>
          <p className="text-xl text-gray-400">Simulador de escenarios de riesgo</p>
        </div>
        <div className="flex items-center justify-end">
          <div className={`px-4 py-2 rounded-lg font-bold text-lg ${getRiskColor(currentRisk)}`}>
            Riesgo simulado: {currentRisk}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl shadow-lg mb-8">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-blue-400">Variables de simulación</h2>
            <button onClick={() => setModalOpen(true)} className="text-gray-400 hover:text-white">
                <FaInfoCircle size={24} />
            </button>
        </div>
        <div className="flex flex-col md:flex-row gap-6 items-center">
            <SimulationSlider label="Ingresos (en miles USD)" value={simulatedValues.ingresos} onChange={(e) => handleSliderChange('ingresos', e.target.value)} min="10" max="100" unit="k" />
            <SimulationSlider label="Reputación digital" value={simulatedValues.reputacion} onChange={(e) => handleSliderChange('reputacion', e.target.value)} min="0" max="100" unit="%" />
            <SimulationSlider label="Pago a tiempo" value={simulatedValues.pago} onChange={(e) => handleSliderChange('pago', e.target.value)} min="0" max="100" unit="%" />
            <button onClick={handlePrediction} className="bg-blue-600 text-white font-bold py-4 px-6 rounded-lg hover:bg-blue-700 transition duration-300 self-end whitespace-nowrap">
                What if...?
            </button>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
          <h2 className="text-2xl font-bold text-blue-400 mb-4">Análisis de Predicción</h2>
          <div style={{ position: 'relative', height: '60vh' }}>
            <Radar data={predictionData} options={radarChartOptions} />
          </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setModalOpen(false)} title="Cálculo de Variables">
        <div className="text-gray-300 space-y-4">
            <p><strong>Ingresos:</strong> Representa el flujo de ingresos proyectado de la empresa. Un mayor ingreso generalmente disminuye el riesgo.</p>
            <p><strong>Reputación digital:</strong> Mide el sentimiento y la presencia en línea de la marca. Se calcula analizando menciones, reseñas y perfiles sociales.</p>
            <p><strong>Pago a tiempo:</strong> Es el porcentaje histórico de pagos a proveedores y créditos realizados antes de la fecha de vencimiento.</p>
        </div>
      </Modal>
    </div>
  );
};

export default Simulation;
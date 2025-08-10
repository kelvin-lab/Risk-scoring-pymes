import { useState, useEffect } from 'react';
import { getScoringResult } from '../services/scoringAPI';
import { Radar } from 'react-chartjs-2';
import { FaInfoCircle } from 'react-icons/fa';

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

  useEffect(() => {
    const data = getScoringResult();
    setInitialData(data);
    // Set initial chart data
    setPredictionData({
        labels: data.riskFactors.map(f => f.subject),
        datasets: [
            {
                label: 'Predicción Actual',
                data: data.riskFactors.map(f => f.A),
                backgroundColor: 'rgba(42, 71, 91, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
            }
        ]
    });
  }, []);

  const handleSliderChange = (key, value) => {
    setSimulatedValues(prev => ({ ...prev, [key]: Number(value) }));
  };

  const handlePrediction = () => {
    const { ingresos, reputacion, pago } = simulatedValues;
    
    // Dummy logic for risk calculation
    let newRisk = 'Alto';
    if (ingresos > 70 && reputacion > 80 && pago > 95) newRisk = 'Bajo';
    else if (ingresos > 40 || reputacion > 60) newRisk = 'Medio';
    setCurrentRisk(newRisk);

    // Dummy logic to generate new chart data
    const newChartData = initialData.riskFactors.map(factor => {
        const baseValue = factor.A;
        const boost = (ingresos / 100) + (reputacion / 100) + (pago / 100);
        return Math.min(150, baseValue * boost * 0.5);
    });

    setPredictionData({
        ...predictionData,
        datasets: [
            {
                ...predictionData.datasets[0],
                data: newChartData,
                label: 'Nueva Predicción',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
            }
        ]
    });
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

  if (!initialData || !predictionData) {
    return <div className="text-center text-white">Cargando datos de simulación...</div>;
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen p-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2">
          <h1 className="text-4xl font-bold">Nombre de la empresa</h1>
          <p className="text-xl text-gray-400">Simulador de Escenarios de Riesgo</p>
        </div>
        <div className="flex items-center justify-end">
          <div className={`px-4 py-2 rounded-lg font-bold text-lg ${getRiskColor(currentRisk)}`}>
            Riesgo Simulado: {currentRisk}
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


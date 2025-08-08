import { useState } from 'react';
import { getScoringResult } from '../services/scoringAPI';

const Simulation = () => {
  const initialData = getScoringResult();
  const [income, setIncome] = useState(50000);
  const [reputation, setReputation] = useState(75);
  const [payment, setPayment] = useState(90);

  // Dummy simulation logic
  const simulatedScore = () => {
    if (income > 60000 && reputation > 80 && payment > 95) return 'Bajo';
    if (income > 40000 || reputation > 60) return 'Medio';
    return 'Alto';
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Simulación de Escenarios</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">Ingresos</label>
          <input type="range" min="10000" max="100000" value={income} onChange={(e) => setIncome(e.target.value)} className="w-full" />
          <span>${income}</span>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Reputación Digital (%)</label>
          <input type="range" min="0" max="100" value={reputation} onChange={(e) => setReputation(e.target.value)} className="w-full" />
          <span>{reputation}%</span>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Pago a Tiempo (%)</label>
          <input type="range" min="0" max="100" value={payment} onChange={(e) => setPayment(e.target.value)} className="w-full" />
          <span>{payment}%</span>
        </div>
      </div>
      <div className="p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold">Resultado de la Simulación</h2>
        <p>Puntaje de Riesgo: {simulatedScore()}</p>
      </div>
    </div>
  );
};

export default Simulation;
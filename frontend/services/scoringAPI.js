import axios from 'axios';

const API_URL = import.meta.env.VITE_IA_ANALYZER_API_URL;

export const uploadRequest = async (formData) => {
  console.log('Uploading request to:', API_URL);
  console.log([...formData.entries()]);

  try {
    const response = await axios.post(API_URL, formData, {
      timeout: 300000, // 5 minutes timeout
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading request:');
    throw error;
  }
};

export const getScoringResult = () => {
  return {
    riskScore: 'Medio',
    creditSuggested: 8000,
    factors: ['ventas', 'reputación'],
    industryComparison: [
      { name: 'Sector A', uv: 4000, pv: 2400, amt: 2400 },
      { name: 'Tu empresa', uv: 2000, pv: 9800, amt: 2290 },
    ],
    riskFactors: [
        { subject: 'Ventas', A: 120, fullMark: 150 },
        { subject: 'Reputación', A: 98, fullMark: 150 },
        { subject: 'Liquidez', A: 86, fullMark: 150 },
        { subject: 'Endeudamiento', A: 99, fullMark: 150 },
        { subject: 'Activos', A: 85, fullMark: 150 },
      ],
    summary: 'Este es un resumen de ejemplo basado en datos de prueba. La empresa muestra un perfil de riesgo medio con un crédito sugerido de 8000.'
  };
};

export const getSimulationResult = async (simulationData) => {
  const API_URL = import.meta.env.VITE_IA_SIMULATION_API_URL;
  console.log('Sending simulation data to:', API_URL);
  console.log(simulationData);

  try {
    const response = await axios.post(API_URL, simulationData, {
      timeout: 300000, // 5 minutes timeout
    });
    return response.data;
  } catch (error) {
    console.error('Error getting simulation result:', error);
    throw error;
  }
};

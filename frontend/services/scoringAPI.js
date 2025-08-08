import axios from 'axios';

const API_URL = 'http://';

export const uploadRequest = (formData) => {
  console.log('Uploading data:', formData);
  return Promise.resolve();
};

export const getScoringResult = () => {
  //Formato base para el scoring - Definido el formato del payload se adaptará esta solucion
  return {
    riskScore: 'Medio',
    creditSuggested: 8000,
    factors: ['ventas', 'reputación'],
    industryComparison: [
      { name: 'Sector A', uv: 4000, pv: 2400, amt: 2400 },
      { name: 'Sector B', uv: 3000, pv: 1398, amt: 2210 },
      { name: 'Tu Empresa', uv: 2000, pv: 9800, amt: 2290 },
    ],
    riskFactors: [
        { subject: 'Ventas', A: 120, B: 110, fullMark: 150 },
        { subject: 'Reputación', A: 98, B: 130, fullMark: 150 },
        { subject: 'Liquidez', A: 86, B: 130, fullMark: 150 },
        { subject: 'Endeudamiento', A: 99, B: 100, fullMark: 150 },
        { subject: 'Activos', A: 85, B: 90, fullMark: 150 },
      ],
  };
};

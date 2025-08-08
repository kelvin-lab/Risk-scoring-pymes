import { getScoringResult } from '../services/scoringAPI';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const data = getScoringResult();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard de Riesgo</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-4 bg-white rounded-lg shadow">Risk Score: {data.riskScore}</div>
        <div className="p-4 bg-white rounded-lg shadow">Credit Suggested: ${data.creditSuggested}</div>
        <div className="p-4 bg-white rounded-lg shadow">Key Factors: {data.factors.join(', ')}</div>
      </div>
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 bg-white rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Comparativa del Sector</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.industryComparison}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="pv" fill="#8884d8" />
              <Bar dataKey="uv" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="p-4 bg-white rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Factores de Riesgo</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data.riskFactors}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis />
              <Radar name="Mike" dataKey="A" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
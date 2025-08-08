import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadRequest } from '../services/scoringAPI';

const UploadRequest = () => {
  const [companyName, setCompanyName] = useState('');
  const [file, setFile] = useState(null);
  const [socialUrl, setSocialUrl] = useState('');
  const [references, setReferences] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('companyName', companyName);
    formData.append('file', file);
    formData.append('socialUrl', socialUrl);
    formData.append('references', references);

    // Simulating API call
    await uploadRequest(formData);
    navigate('/dashboard');
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Nueva Evaluación de Riesgo</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Nombre de la Empresa</label>
          <input type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Archivo Financiero (Supercias)</label>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">URL de Red Social (Facebook o Instagram)</label>
          <input type="url" value={socialUrl} onChange={(e) => setSocialUrl(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Referencias (Opcional)</label>
          <textarea value={references} onChange={(e) => setReferences(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"></textarea>
        </div>
        <button type="submit" className="bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 transition duration-300">Enviar</button>
      </form>
    </div>
  );
};

export default UploadRequest;
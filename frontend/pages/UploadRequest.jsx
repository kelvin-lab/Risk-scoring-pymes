import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadRequest } from '../services/scoringAPI';
import { 
    FaInstagram, FaFacebook, FaTiktok, FaBuilding, FaStore, 
    FaCity, FaGlobeAmericas, FaMapMarkerAlt, FaFilePdf, FaFileCsv 
} from 'react-icons/fa';

const IconInput = ({ icon, ...props }) => (
    <div className="relative flex items-center">
        <span className="absolute left-3 w-5 h-5 text-gray-400">{icon}</span>
        <input {...props} className="pl-10 block w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-md text-white shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
    </div>
);

const FileInput = ({ icon, label, ...props }) => (
    <div className="relative">
        <label className="block text-sm font-medium text-gray-300 mb-2">{label}</label>
        <div className="relative flex items-center">
            <span className="absolute left-3 w-5 h-5 text-gray-400">{icon}</span>
            <input {...props} className="pl-10 block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-blue-300 hover:file:bg-gray-600" />
        </div>
    </div>
);

const UploadRequest = () => {
  const [razonSocial, setRazonSocial] = useState('');
  const [nombreComercial, setNombreComercial] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [pais, setPais] = useState('Ecuador');
  const [address, setAddress] = useState('');
  const [socialLinks, setSocialLinks] = useState({ instagram: '', facebook: '', tiktok: '' });
  const [referenceFiles, setReferenceFiles] = useState([]);
  const [financialFiles, setFinancialFiles] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSocialLinkChange = (platform, value) => {
    setSocialLinks(prev => ({ ...prev, [platform]: value }));
  };

  const handleFileChange = (e, setFiles, maxFiles) => {
    const files = Array.from(e.target.files);
    if (files.length > maxFiles) {
      setError(`Error: No puedes subir más de ${maxFiles} archivos.`);
      e.target.value = null;
    } else {
      setError('');
      setFiles(files);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (error) {
      alert(error);
      return;
    }
    // ... (formData logic would be updated here)
    console.log('Submitting...');
    await uploadRequest(new FormData());
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-gray-800 rounded-xl shadow-lg p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Formulario de Solicitud</h1>
          <p className="text-gray-400">Completa los datos para iniciar la evaluación de riesgo.</p>
        </div>

        {error && <div className="bg-red-500 text-white p-3 rounded-md mb-6">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
            <IconInput icon={<FaBuilding />} type="text" placeholder="Razón Social" value={razonSocial} onChange={(e) => setRazonSocial(e.target.value)} required />
            <IconInput icon={<FaStore />} type="text" placeholder="Nombre Comercial" value={nombreComercial} onChange={(e) => setNombreComercial(e.target.value)} required />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative">
                    <IconInput icon={<FaGlobeAmericas />} type="text" placeholder="País" value={pais} readOnly />
                    <p className="text-xs text-gray-500 mt-1 pl-2">Por el momento, solo operamos en Ecuador.</p>
                </div>
                <div>
                  <IconInput icon={<FaCity />} type="text" placeholder="Ciudad" value={ciudad} onChange={(e) => setCiudad(e.target.value)} required />
                    <p className="text-xs text-gray-500 mt-1 pl-2"></p>
                </div>
            </div>
            <IconInput icon={<FaMapMarkerAlt />} type="text" placeholder="Dirección" value={address} onChange={(e) => setAddress(e.target.value)} required />
            
            <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Perfiles de Redes Sociales</label>
                <div className="space-y-3">
                    <IconInput icon={<FaInstagram />} placeholder="URL de Instagram" value={socialLinks.instagram} onChange={(e) => handleSocialLinkChange('instagram', e.target.value)} />
                    <IconInput icon={<FaFacebook />} placeholder="URL de Facebook" value={socialLinks.facebook} onChange={(e) => handleSocialLinkChange('facebook', e.target.value)} />
                    <IconInput icon={<FaTiktok />} placeholder="URL de TikTok" value={socialLinks.tiktok} onChange={(e) => handleSocialLinkChange('tiktok', e.target.value)} />
                </div>
            </div>

            <FileInput icon={<FaFilePdf />} label="Referencias (hasta 3 archivos PDF)" type="file" multiple accept=".pdf" onChange={(e) => handleFileChange(e, setReferenceFiles, 3)} />
            <FileInput icon={<FaFileCsv />} label="Archivo Financiero (hasta 3 PDF o CSV)" type="file" multiple accept=".pdf,.csv" onChange={(e) => handleFileChange(e, setFinancialFiles, 3)} required />

            <button type="submit" className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-md hover:bg-blue-700 transition duration-300 disabled:opacity-50">Enviar para Análisis</button>
        </form>
      </div>
    </div>
  );
};

export default UploadRequest;


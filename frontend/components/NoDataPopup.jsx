import { Link } from 'react-router-dom';

const NoDataPopup = ({ message, to, buttonText }) => {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex flex-col justify-center items-center z-50">
            <div className="bg-gray-800 rounded-lg shadow-xl p-8 max-w-sm text-center">
                <h2 className="text-center text-white text-xl font-semibold mb-4">No hay datos</h2>
                <p className="text-center text-white mb-6">{message}</p>
                <Link to={to}>
                    <button className="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-300">
                        {buttonText}
                    </button>
                </Link>
            </div>
        </div>
    );
};

export default NoDataPopup;

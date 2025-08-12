import { useState, useEffect } from 'react';

const funnyMessages = [
    "Enviando datos a la Matrix...",
    "Consultando a los dioses del crédito...",
    "Midiendo el cosmos financiero...",
    "No te preocupes, nuestros monos entrenados están en ello...",
    "Calculando si tu unicornio es financieramente viable...",
    "Alineando los chakras de tus finanzas...",
    "Alimentando al hamster que potencia nuestros servidores...",
    "Haciendo una danza de la lluvia de datos...",
    "Cargando... Por favor, espera o trae un café.",
    "Nuestros algoritmos están discutiendo sobre ti. Parecen contentos."
];

const LoadingPopup = () => {
    const [message, setMessage] = useState(funnyMessages[0]);

    useEffect(() => {
        const interval = setInterval(() => {
            setMessage(funnyMessages[Math.floor(Math.random() * funnyMessages.length)]);
        }, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex flex-col justify-center items-center z-50">
            <div className="loader ease-linear rounded-full border-8 border-t-8 border-gray-200 h-32 w-32 mb-4"></div>
            <h2 className="text-center text-white text-xl font-semibold">Analizando...</h2>
            <p className="text-center text-white w-1/3 mt-2">{message}</p>
        </div>
    );
};

export default LoadingPopup;

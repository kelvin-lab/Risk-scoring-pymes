import { Link } from 'react-router-dom';
import Atropos from 'atropos/react';
import 'atropos/css';
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/autoplay';
import { Autoplay } from 'swiper/modules';

const Home = () => {
  const handleScroll = (e, targetId) => {
    e.preventDefault();
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      window.scrollTo({
        top: targetElement.offsetTop,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="text-white bg-gray-900">
      <div className="w-full pt-2 pb-10 flex flex-col items-center justify-center text-center">
        <h1 className="text-5xl md:text-7xl font-bold mb-4 text-shadow-lg">Scoring AlfaTech</h1>
        <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl mx-auto px-4">
          Evaluación de riesgo para PYMEs con IA. Analizamos comportamiento digital, referencias y estados financieros para ofrecer un puntaje de riesgo y recomendación de crédito.
        </p>
        <div className="space-x-4 mb-12">
          <Link to="/upload-request">
            <button className="bg-blue-600 text-white font-bold py-3 px-8 rounded-full hover:bg-blue-700 transition duration-300 text-lg">
              Iniciar evaluación
            </button>
          </Link>
          <a href="#how-it-works"  className="text-blue-400 hover:text-blue-300 transition duration-300 text-lg">
            Cómo funciona
          </a>
        </div>

        <Atropos
          className="w-10/12 md:w-8/12 lg:w-4/12 h-auto"
          shadowScale={1.02}
          activeOffset={40}
        >
          <img 
            src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80"
            alt="Financial Analysis Dashboard"
            className="rounded-lg shadow-2xl"
          />
        </Atropos>
      </div>

      <section className="py-16 bg-gray-800 rounded-lg">
        <div className="container mx-auto">
          <h3 className="text-center text-2xl font-semibold mb-8 text-gray-200">Empresas que confían en nosotros</h3>
          <Swiper
            modules={[Autoplay]}
            spaceBetween={50}
            slidesPerView={5}
            loop={true}
            autoplay={{
              delay: 2500,
              disableOnInteraction: false,
            }}
            breakpoints={{
              320: { slidesPerView: 2, spaceBetween: 20 },
              640: { slidesPerView: 3, spaceBetween: 30 },
              768: { slidesPerView: 4, spaceBetween: 40 },
              1024: { slidesPerView: 5, spaceBetween: 50 },
            }}
          >
            {[...Array(6)].map((_, i) => (
              <SwiperSlide key={i} className="flex items-center justify-center">
                <img src="/LOGO-ALFANET.png" alt={`Cliente ${i + 1}`} className="h-20" />
              </SwiperSlide>
            ))}
          </Swiper>
        </div>
      </section>

      <section id="how-it-works" className="py-12 bg-gray-900">
        <div className="container mx-auto text-center">
          <h2 className="text-4xl font-bold mb-10">¿Cómo funciona?</h2>
          <div className="grid md:grid-cols-3 gap-10 px-4">
            <div className="bg-gray-800 p-8 rounded-lg">
              <h3 className="text-2xl font-bold mb-4 text-blue-400">1. Sube tus Datos</h3>
              <p>Completa el formulario con la información de tu empresa, redes sociales y documentos financieros.</p>
            </div>
            <div className="bg-gray-800 p-8 rounded-lg">
              <h3 className="text-2xl font-bold mb-4 text-blue-400">2. Análisis con IA</h3>
              <p>Nuestro modelo de IA procesa la información para evaluar el riesgo crediticio de manera integral.</p>
            </div>
            <div className="bg-gray-800 p-8 rounded-lg">
              <h3 className="text-2xl font-bold mb-4 text-blue-400">3. Obtén tu Scoring</h3>
              <p>Recibe un puntaje de riesgo, una recomendación de crédito y un análisis detallado en tu dashboard.</p>
            </div>
          </div>
        </div>
      </section>
      <div className="space-x-4 mb-4 mt-2 flex justify-center">
        <Link to="/upload-request">
          <button className="bg-blue-600 text-white font-bold py-3 px-8 rounded-full hover:bg-blue-700 transition duration-300 text-lg">
            Iniciar evaluación
          </button>
        </Link>
      </div>
    </div>
  );
};

export default Home;


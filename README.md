# Evaluación de riesgo financiero para PYMEs mediante fuentes de datos alternativas e inteligencia artificial

## Descripción del proyecto
Este proyecto tiene como objetivo desarrollar una plataforma basada en inteligencia artificial capaz de evaluar el riesgo financiero de pequeñas y medianas empresas (PYMEs) utilizando fuentes de información no tradicionales, tales como comportamiento digital, reputación en redes sociales y referencias comerciales.  
El propósito es ofrecer a las instituciones financieras una herramienta más inclusiva y precisa para determinar la viabilidad crediticia de empresas que carecen de historial financiero formal, reduciendo la exclusión y mejorando la toma de decisiones.

La solución combina técnicas de **procesamiento de lenguaje natural (NLP)**, **modelado predictivo**, **análisis de datos estructurados y no estructurados** y visualización interactiva de resultados, permitiendo obtener un puntaje de riesgo acompañado de explicaciones e indicadores clave.

---

## Funcionalidades principales
- **Ingesta y normalización de datos**: recepción de estados financieros, enlaces de redes sociales y referencias comerciales; limpieza y estandarización de la información.
- **Extracción y análisis de información no estructurada**: uso de web scraping y NLP para procesar publicaciones, comentarios y reseñas en redes sociales.
- **Generación de puntaje de riesgo**: aplicación de modelos de IA para calcular un “scoring alternativo” que clasifica el riesgo como alto, medio o bajo.
- **Visualización de resultados**: dashboard interactivo con métricas financieras, comparativas sectoriales y factores determinantes del puntaje.
- **Simulación de escenarios**: análisis de impacto de variaciones en ventas, reputación digital o comportamiento de pago sobre el nivel de riesgo.

## Tecnologías Utilizadas

### Frontend
- **React**: Framework principal para la construcción de la interfaz de usuario
- **Vite**: Herramienta de construcción y desarrollo que proporciona un entorno de desarrollo más rápido
- **TailwindCSS**: Framework de CSS utilizado para el diseño y estilizado de la aplicación
- **Chart.js y React-Chartjs-2**: Bibliotecas para la creación de gráficos y visualizaciones interactivas
- **Axios**: Cliente HTTP para realizar peticiones al backend
- **React Icons**: Biblioteca de iconos para la interfaz de usuario
- **Atropos**: Efectos visuales y animaciones para mejorar la experiencia de usuario
- **Swiper**: Componente de carrusel para mostrar contenido deslizable

## Instrucciones de Uso

### Requisitos Previos
- Node.js (versión 18 o superior)
- npm (incluido con Node.js)

### Configuración del Frontend

1. **Instalación de dependencias**
   ```bash
   cd frontend
   npm install
    ```
2. **Configuración de variables de entorno**
   - Crea un archivo `.env` en el directorio `frontend` basado en `.env.example`
   - Configura las variables necesarias para la conexión con el backend

3. **Iniciar el servidor de desarrollo**
   ```bash
   npm run dev
   ```
   La aplicación estará disponible en `http://localhost:5173`

### Uso de la Aplicación

1. **Página de Inicio**
   - Accede a la página principal para ver una descripción general del servicio
   - Utiliza el botón "Iniciar evaluación" para comenzar un nuevo análisis

2. **Nueva Evaluación**
   - Completa el formulario con la información de la empresa
   - Sube los documentos financieros requeridos (formato PDF)
   - Proporciona los enlaces a redes sociales para el análisis de reputación digital

3. **Dashboard**
   - Visualiza el puntaje de riesgo y la recomendación de crédito
   - Explora los gráficos interactivos con métricas y comparativas
   - Analiza los factores clave que influyen en la evaluación

4. **Simulador**
   - Utiliza el simulador para evaluar diferentes escenarios
   - Ajusta las variables de ingresos, reputación y pagos
   - Observa cómo los cambios afectan al puntaje de riesgo

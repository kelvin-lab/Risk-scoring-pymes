from typing import Dict

def parse_financials_from_file(file_path: str) -> Dict:
    """
    Procesa un balance o estado financiero desde un archivo PDF/XLSX
    y devuelve métricas clave en un dict.
    🚧 Actualmente devuelve datos de ejemplo (mock).
    """
    # Aquí en el futuro leeremos y extraeremos las métricas reales
    return {
        "ventas_anuales": 350000.0,
        "margen_bruto": 0.33,
        "razon_corriente": 1.6,
        "deuda_total_activos": 0.42,
        "flujo_caja_operativo": 28000.0
    }

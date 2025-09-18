# Sports Odds Scraper

**Sports Odds Scraper** es un proyecto que extrae información de *odds* deportivos desde URLs predefinidas, utilizando técnicas de web scraping. La información extraída se parsea desde el HTML y se expone en un endpoint JSON mediante una API construida con FastAPI.

## Tabla de Contenidos
- [Descripción](#descripción)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Funcionalidades](#funcionalidades)
- [Estado del Proyecto](#estado-del-proyecto)
- [Tareas Pendientes](#tareas-pendientes)
- [Instalación](#instalación)
- [Uso](#uso)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## Descripción
Este proyecto es un *web scraper* diseñado para navegar a URLs específicas, extraer información de *odds* deportivos mediante el análisis del HTML con BeautifulSoup (BS4), y exponer los datos en un endpoint JSON utilizando FastAPI. Actualmente, el proyecto soporta la extracción de datos para DraftKings a través del endpoint `/v1/draftkings`, con planes para expandir su funcionalidad a otros proveedores y deportes.

## Tecnologías Utilizadas
- **Python 3.12**: Lenguaje principal del proyecto.
- **Selenium (WebDriver)**: Automatización de navegadores para navegar y extraer contenido dinámico.
- **FastAPI**: Framework para construir endpoints API rápidos y eficientes.
- **BeautifulSoup (BS4)**: Librería para parsear y extraer información del HTML.

## Funcionalidades
- Navega a URLs predefinidas para recolectar datos de *odds* deportivos.
- Extrae información específica de las clases HTML utilizando BS4.
- Expone los datos recolectados en un endpoint JSON (`/v1/draftkings`).
- Estructura modular para facilitar la adición de nuevos proveedores y deportes.

## Estado del Proyecto
- **Versión actual**: v1
  - El endpoint `/v1/draftkings` está completamente funcional.
- **En desarrollo**:
  - Soporte para otros proveedores de *odds* deportivos.
  - Mejora en la estructura de los endpoints para mayor escalabilidad.

## Tareas Pendientes
- Definir si el proyecto se enfocará en un único proveedor o soportará múltiples proveedores.
- Diseñar una estructura más robusta para los endpoints de la API.
- Ampliar la cobertura para incluir más deportes y fuentes de datos.
- Mejorar la documentación y ejemplos de uso.

## Instalación
Sigue estos pasos para configurar el proyecto localmente:

1. **Clona el repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd sports-odds-scraper

python -m venv venv
source venv/bin/activate

uvicorn main:app --reload
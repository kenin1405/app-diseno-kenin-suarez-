# Aplicación de Diseño Experimental

Aplicación multipágina desarrollada con Streamlit como apoyo para el aprendizaje
de diseños experimentales aplicados a problemas de Ingeniería Agrícola. Incluye
análisis de un Diseño Completamente al Azar (DCA), comparación de tratamientos y
diagnóstico de supuestos. Los resultados deben interpretarse y verificarse por
el estudiante.

## Módulos

| Módulo | Estado | Descripción |
|---|---|---|
| DCA — Diseño completamente al azar | Disponible | Análisis de un factor, comparaciones de Tukey y diagnóstico de supuestos. |
| DBCA — Diseño de bloques completos al azar | En construcción | Compara tratamientos controlando una fuente de variación por bloques. |
| DCL — Diseño de cuadrado latino | En construcción | Compara tratamientos controlando dos fuentes de variación. |
| DPD — Diseño de parcelas divididas | En construcción | Estudia factores asignados a parcelas principales y subparcelas. |
| Factoriales | En construcción | Estudia varios factores y sus interacciones. |
| RSM — Metodología de superficie de respuesta | En construcción | Modela y optimiza respuestas respecto a factores cuantitativos. |

## Estructura del proyecto

```text
.
├── app.py                       # Portada y navegación multipágina
├── data/
│   └── dca_secadores.csv        # Datos de ejemplo de humedad de yuca
├── pages/                       # Páginas de los módulos de Streamlit
├── utils/
│   ├── anova_utils.py           # Análisis del DCA
│   └── diagnostico_utils.py     # Diagnóstico de supuestos
├── verificacion/
│   └── verificacion_dca.R       # Verificación independiente en R
├── requirements.txt             # Dependencias de Python
└── README.md
```

## Instalación y ejecución

### VS Code local en Windows (PowerShell)

Desde la carpeta raíz del proyecto, crea y activa el entorno virtual e instala
las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Con el entorno activado, inicia la aplicación:

```powershell
streamlit run app.py
```

### GitHub Codespaces

Desde la terminal del Codespace, instala las dependencias y ejecuta la app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección local y la opción para abrir la aplicación en el
navegador.

## Verificación opcional en R

El script `verificacion/verificacion_dca.R` verifica un conjunto de datos
alternativo llamado `data/dca_mi_variante.csv`, que debe contener las columnas
`secador` y `humedad`. El archivo no se incluye en el repositorio. Con R
instalado, ejecuta el script desde la carpeta `verificacion/`:

```bash
cd verificacion
Rscript verificacion_dca.R
```

El script imprime la tabla ANOVA, las medias por secador, el coeficiente de
variación y las comparaciones de Tukey.

## Autor

**Kenin David Suarez Angel** — Ingeniería Agrícola, Universidad de Sucre.

## Declaración de uso de IA

Se utilizó GitHub Copilot como asistente de IA para apoyar la preparación de la
estructura del proyecto, la interfaz de Streamlit, las utilidades de análisis y
diagnóstico, y esta documentación. Las salidas estadísticas y el código deben
ser revisados y contrastados con los fundamentos del curso y los cálculos
manuales antes de usarse en decisiones experimentales.

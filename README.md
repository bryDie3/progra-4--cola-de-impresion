# 🖨 Simulador de Cola de Impresión

Simulación de una cola de impresión en Python que aplica la estructura de datos **Queue** para modelar cómo los trabajos llegan, esperan turno y son procesados por una impresora.

---

## Estructura del proyecto

```
print_simulation/
├── queue_ds.py      # Implementación propia de Queue (lista enlazada)
├── models.py        # Clases PrintTask y Printer + generador aleatorio
├── simulation.py    # Motor de simulación (PrintSimulation + SimulationResult)
├── app.py           # Interfaz gráfica con Tkinter
├── tests.py         # Pruebas unitarias
└── README.md
```

---

## Requisitos

- Python 3.10 o superior  
- Tkinter (incluido en la instalación estándar de Python)

---

## Instalación y ejecución

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/print-queue-simulation.git
cd print-queue-simulation/print_simulation

# Ejecutar la interfaz gráfica
python app.py

# Ejecutar las pruebas
python tests.py
```

---

## Descripción de clases

### `Queue` (`queue_ds.py`)
Cola FIFO implementada con una lista enlazada simple (nodos `Node`).  
Operaciones: `enqueue`, `dequeue`, `peek`, `is_empty`, `size`.

### `PrintTask` (`models.py`)
Representa un trabajo de impresión. Atributos:
- `job_id` – identificador único autoincremental
- `pages` – número de páginas
- `arrival_time` – segundo de llegada
- `start_time` / `finish_time` – tiempos de inicio y fin
- `wait_time` – tiempo de espera (derivado)

### `Printer` (`models.py`)
Modela una impresora con velocidad en páginas/minuto.  
Métodos: `start_task`, `tick`, `is_busy`.

### `PrintSimulation` (`simulation.py`)
Motor principal. Itera segundo a segundo:
1. Encola los trabajos que llegan en ese instante.
2. Si la impresora está libre y hay trabajo, lo toma.
3. Avanza la impresora un segundo.

Devuelve un `SimulationResult` con todas las métricas.

---

## Métricas reportadas

| Métrica | Descripción |
|---------|-------------|
| Trabajos procesados | Total de trabajos terminados |
| Páginas impresas | Suma de páginas de todos los trabajos |
| Tiempo prom. de espera | Promedio de segundos en cola |
| Mayor espera | Trabajo con mayor tiempo de espera |
| Tamaño máx. cola | Pico de trabajos en cola simultáneos |
| Tiempo simulado | Duración total de la simulación |

---

## Interfaz gráfica

La interfaz (`app.py`) permite:
- Configurar duración, probabilidad de llegada, rango de páginas, velocidad de impresora y semilla aleatoria.
- Iniciar, detener y limpiar la simulación.
- Ver en tiempo real el estado de la impresora y la cola visual.
- Consultar el registro de eventos con colores por tipo.
- Ver las métricas finales al terminar.

---

## Pruebas

```bash
python tests.py
```

Cubren:
- Operaciones FIFO de `Queue`
- Validaciones de `PrintTask` y `Printer`
- Simulación vacía, trabajo único, orden FIFO, crecimiento de cola y métricas

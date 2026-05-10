"""
models.py – Clases PrintTask y Printer para la simulación de cola de impresión.
"""

import random


# ─────────────────────────────────────────────────────────────────────────────
#  PrintTask
# ─────────────────────────────────────────────────────────────────────────────

class PrintTask:
    """Representa un trabajo de impresión."""

    _id_counter = 0

    def __init__(self, pages: int, arrival_time: int, job_id: int = None):
        """
        Parameters
        ----------
        pages        : número de páginas del trabajo (> 0)
        arrival_time : segundo de simulación en que llegó el trabajo
        job_id       : identificador único (se auto-genera si no se pasa)
        """
        if pages <= 0:
            raise ValueError(f"El número de páginas debe ser positivo, se recibió: {pages}")
        if arrival_time < 0:
            raise ValueError(f"El tiempo de llegada no puede ser negativo: {arrival_time}")

        PrintTask._id_counter += 1
        self.job_id = job_id if job_id is not None else PrintTask._id_counter
        self.pages = pages
        self.arrival_time = arrival_time

        # Se rellena cuando la impresora lo toma
        self.start_time: int | None = None
        self.finish_time: int | None = None

    # ------------------------------------------------------------------ #

    @property
    def wait_time(self) -> int | None:
        """Segundos que esperó en cola antes de empezar a imprimirse."""
        if self.start_time is None:
            return None
        return self.start_time - self.arrival_time

    @property
    def total_time(self) -> int | None:
        """Tiempo total desde llegada hasta fin de impresión."""
        if self.finish_time is None:
            return None
        return self.finish_time - self.arrival_time

    @classmethod
    def reset_counter(cls):
        cls._id_counter = 0

    def __repr__(self):
        return (f"PrintTask(id={self.job_id}, pages={self.pages}, "
                f"arrival={self.arrival_time})")


# ─────────────────────────────────────────────────────────────────────────────
#  Printer
# ─────────────────────────────────────────────────────────────────────────────

class Printer:
    """
    Modela una impresora con velocidad configurable (páginas por minuto).
    Procesa un trabajo a la vez; mientras está ocupada rechaza nuevos trabajos.
    """

    def __init__(self, pages_per_minute: int = 10):
        """
        Parameters
        ----------
        pages_per_minute : velocidad de la impresora (páginas/minuto)
        """
        if pages_per_minute <= 0:
            raise ValueError("La velocidad de la impresora debe ser positiva.")
        self.pages_per_minute = pages_per_minute
        self._current_task: PrintTask | None = None
        self._time_remaining: int = 0          # segundos restantes para terminar

    # ------------------------------------------------------------------ #

    def is_busy(self) -> bool:
        return self._current_task is not None

    def start_task(self, task: PrintTask, current_time: int):
        """Inicia el procesamiento de un trabajo."""
        if self.is_busy():
            raise RuntimeError("La impresora ya está ocupada.")
        task.start_time = current_time
        self._current_task = task
        # Convertir páginas/minuto → segundos por página
        seconds_per_page = 60 / self.pages_per_minute
        self._time_remaining = int(task.pages * seconds_per_page)

    def tick(self, current_time: int) -> PrintTask | None:
        """
        Avanza un segundo en la simulación.
        Devuelve el trabajo terminado si lo hay, None si sigue en proceso.
        """
        if not self.is_busy():
            return None
        self._time_remaining -= 1
        if self._time_remaining <= 0:
            finished = self._current_task
            finished.finish_time = current_time
            self._current_task = None
            self._time_remaining = 0
            return finished
        return None

    @property
    def current_task(self) -> PrintTask | None:
        return self._current_task

    @property
    def time_remaining(self) -> int:
        return self._time_remaining

    def __repr__(self):
        status = f"ocupada (faltan {self._time_remaining}s)" if self.is_busy() else "libre"
        return f"Printer(ppm={self.pages_per_minute}, estado={status})"


# ─────────────────────────────────────────────────────────────────────────────
#  Generador de trabajos aleatorios (helper)
# ─────────────────────────────────────────────────────────────────────────────

def generate_random_tasks(
    duration: int,
    arrival_probability: float = 0.1,
    min_pages: int = 1,
    max_pages: int = 20,
    seed: int | None = None,
) -> list[PrintTask]:
    """
    Genera una lista de PrintTask con llegadas estocásticas.

    Parameters
    ----------
    duration             : duración de la simulación en segundos
    arrival_probability  : probabilidad de que llegue un trabajo en cada segundo
    min_pages / max_pages: rango de páginas por trabajo
    seed                 : semilla para reproducibilidad
    """
    if not (0 < arrival_probability <= 1):
        raise ValueError("La probabilidad de llegada debe estar en (0, 1].")
    if min_pages > max_pages:
        raise ValueError("min_pages no puede ser mayor que max_pages.")

    rng = random.Random(seed)
    PrintTask.reset_counter()
    tasks = []
    for t in range(duration):
        if rng.random() < arrival_probability:
            pages = rng.randint(min_pages, max_pages)
            tasks.append(PrintTask(pages=pages, arrival_time=t))
    return tasks

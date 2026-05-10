"""
simulation.py – Motor de simulación de la cola de impresión.
"""

from queue_ds import Queue
from models import PrintTask, Printer


class SimulationResult:
    """Contiene todas las métricas calculadas al finalizar la simulación."""

    def __init__(self):
        self.processed_tasks: list[PrintTask] = []
        self.max_queue_size: int = 0
        self.total_seconds: int = 0

    # ------------------------------------------------------------------ #
    #  Métricas derivadas                                                  #
    # ------------------------------------------------------------------ #

    @property
    def total_jobs(self) -> int:
        return len(self.processed_tasks)

    @property
    def average_wait_time(self) -> float:
        if not self.processed_tasks:
            return 0.0
        return sum(t.wait_time for t in self.processed_tasks) / len(self.processed_tasks)

    @property
    def max_wait_task(self) -> PrintTask | None:
        if not self.processed_tasks:
            return None
        return max(self.processed_tasks, key=lambda t: t.wait_time)

    @property
    def total_pages_printed(self) -> int:
        return sum(t.pages for t in self.processed_tasks)

    def summary(self) -> str:
        lines = [
            "═" * 52,
            "   RESULTADOS DE LA SIMULACIÓN",
            "═" * 52,
            f"  Duración simulada      : {self.total_seconds} segundos",
            f"  Trabajos procesados    : {self.total_jobs}",
            f"  Páginas impresas       : {self.total_pages_printed}",
            f"  Tamaño máx. de cola   : {self.max_queue_size}",
            f"  Tiempo prom. de espera : {self.average_wait_time:.2f} s",
        ]
        if self.max_wait_task:
            mw = self.max_wait_task
            lines.append(
                f"  Mayor espera           : Trabajo #{mw.job_id} "
                f"({mw.pages} pág.) → {mw.wait_time} s"
            )
        lines.append("═" * 52)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────

class PrintSimulation:
    """
    Orquesta la simulación segundo a segundo.

    Parameters
    ----------
    tasks              : lista de PrintTask ordenada por arrival_time
    pages_per_minute   : velocidad de la impresora
    verbose            : si True imprime log por consola
    callback           : función opcional que recibe eventos durante la simulación
                        firma: callback(event_type: str, data: dict)
    """

    def __init__(
        self,
        tasks: list[PrintTask],
        pages_per_minute: int = 10,
        verbose: bool = False,
        callback=None,
    ):
        if not isinstance(tasks, list):
            raise TypeError("tasks debe ser una lista de PrintTask.")
        self.tasks = sorted(tasks, key=lambda t: t.arrival_time)
        self.printer = Printer(pages_per_minute=pages_per_minute)
        self.verbose = verbose
        self.callback = callback

    # ------------------------------------------------------------------ #

    def run(self) -> SimulationResult:
        """Ejecuta la simulación y devuelve SimulationResult."""
        if not self.tasks:
            result = SimulationResult()
            result.total_seconds = 0
            return result

        queue: Queue = Queue()
        result = SimulationResult()

        # Determinar duración: hasta que la impresora procese el último trabajo
        # (puede ser mayor que el último arrival_time)
        task_index = 0
        total_tasks = len(self.tasks)

        # Calculamos un límite superior seguro
        max_time = self.tasks[-1].arrival_time + sum(
            int(t.pages * 60 / self.printer.pages_per_minute) + 1
            for t in self.tasks
        ) + 1

        for current_time in range(max_time):
            # 1. Enqueue trabajos que llegan en este segundo
            while task_index < total_tasks and \
                    self.tasks[task_index].arrival_time == current_time:
                task = self.tasks[task_index]
                queue.enqueue(task)
                task_index += 1
                self._log(current_time, f"[LLEGADA]  Trabajo #{task.job_id} "
                        f"({task.pages} pág.) ingresó a la cola")
                self._emit("arrival", {"time": current_time, "task": task,
                                    "queue_size": queue.size()})

            # Actualizar tamaño máximo de cola
            if queue.size() > result.max_queue_size:
                result.max_queue_size = queue.size()

            # 2. Si la impresora está libre y hay trabajo, tomar el siguiente
            if not self.printer.is_busy() and not queue.is_empty():
                next_task = queue.dequeue()
                self.printer.start_task(next_task, current_time)
                self._log(current_time, f"[INICIO]   Impresora toma Trabajo "
                        f"#{next_task.job_id} ({next_task.pages} pág.)")
                self._emit("start", {"time": current_time, "task": next_task})

            # 3. Avanzar la impresora un segundo
            finished = self.printer.tick(current_time + 1)
            if finished:
                result.processed_tasks.append(finished)
                self._log(current_time + 1,
                        f"[FIN]      Trabajo #{finished.job_id} terminó. "
                        f"Esperó {finished.wait_time} s")
                self._emit("finish", {"time": current_time + 1,
                                    "task": finished})

            # 4. Condición de término: no quedan trabajos por llegar ni en cola
            #    y la impresora está libre
            if (task_index >= total_tasks
                    and queue.is_empty()
                    and not self.printer.is_busy()):
                result.total_seconds = current_time + 1
                break

        if self.verbose:
            print(result.summary())

        return result

    # ------------------------------------------------------------------ #
    #  Helpers privados                                                    #
    # ------------------------------------------------------------------ #

    def _log(self, t: int, msg: str):
        if self.verbose:
            print(f"  t={t:>6}s  {msg}")

    def _emit(self, event_type: str, data: dict):
        if self.callback:
            self.callback(event_type, data)

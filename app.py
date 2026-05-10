"""
app.py – Interfaz gráfica con Tkinter para la simulación de cola de impresión.
Ejecutar con: python app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import threading
import time
import sys
import os

# Importaciones del proyecto
sys.path.insert(0, os.path.dirname(__file__))
from queue_ds import Queue
from models import PrintTask, Printer, generate_random_tasks
from simulation import PrintSimulation


# ══════════════════════════════════════════════════════════════════════════════
#  Paleta de colores y constantes
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    "bg":          "#0f1117",
    "surface":     "#1a1d27",
    "surface2":    "#252836",
    "accent":      "#6c63ff",
    "accent2":     "#ff6584",
    "green":       "#43d97c",
    "yellow":      "#f5c842",
    "red":         "#ff4757",
    "text":        "#e8eaf0",
    "text_dim":    "#8a8fa8",
    "border":      "#2e3150",
}

FONT_MONO  = ("Courier New", 10)
FONT_TITLE = ("Helvetica", 18, "bold")
FONT_LABEL = ("Helvetica", 10)
FONT_BOLD  = ("Helvetica", 10, "bold")
FONT_SMALL = ("Helvetica", 9)


# ══════════════════════════════════════════════════════════════════════════════
#  Ventana principal
# ══════════════════════════════════════════════════════════════════════════════

class PrintQueueApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("🖨  Simulador de Cola de Impresión")
        self.geometry("1100x720")
        self.minsize(900, 620)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self._sim_thread: threading.Thread | None = None
        self._running = False
        self._log_lines: list[str] = []
        self._events: list[dict] = []   # cola de eventos desde el hilo

        self._build_ui()
        self._apply_ttk_theme()
        self.after(100, self._poll_events)   # polling cada 100 ms

    # ──────────────────────────────────────────────────────────────────────────
    #  Construcción de la UI
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg"], pady=14)
        header.pack(fill="x", padx=24)

        tk.Label(header, text="🖨  Cola de Impresión",
                font=FONT_TITLE, bg=COLORS["bg"],
                fg=COLORS["accent"]).pack(side="left")

        self._status_label = tk.Label(
            header, text="● Listo", font=FONT_BOLD,
            bg=COLORS["bg"], fg=COLORS["green"])
        self._status_label.pack(side="right")

        ttk.Separator(self).pack(fill="x", padx=24)

        # ── Cuerpo ──────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=12)

        # Columna izquierda: configuración + métricas
        left = tk.Frame(body, bg=COLORS["bg"], width=300)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        self._build_config_panel(left)
        self._build_metrics_panel(left)

        # Columna derecha: log + cola visual
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_queue_visual(right)
        self._build_log_panel(right)

    # ── Panel de configuración ───────────────────────────────────────────────

    def _build_config_panel(self, parent):
        card = self._card(parent, "⚙  Configuración")

        fields = [
            ("Duración (seg):",       "duration",    "3600"),
            ("Prob. llegada (0‑1):",  "prob",        "0.10"),
            ("Páginas mín.:",         "min_pages",   "1"),
            ("Páginas máx.:",         "max_pages",   "20"),
            ("Velocidad (pág/min):",  "ppm",         "10"),
            ("Semilla aleatoria:",    "seed",        "42"),
        ]
        self._cfg_vars: dict[str, tk.StringVar] = {}
        for label, key, default in fields:
            row = tk.Frame(card, bg=COLORS["surface"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_SMALL,
                    bg=COLORS["surface"], fg=COLORS["text_dim"],
                    width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            self._cfg_vars[key] = var
            entry = tk.Entry(row, textvariable=var, font=FONT_MONO,
                            bg=COLORS["surface2"], fg=COLORS["text"],
                            insertbackground=COLORS["text"],
                            relief="flat", bd=4, width=10)
            entry.pack(side="right")

        # Botones
        btn_row = tk.Frame(card, bg=COLORS["surface"])
        btn_row.pack(fill="x", pady=(12, 4))

        self._btn_run = self._button(btn_row, "▶  Iniciar",
                                    COLORS["accent"], self._start_simulation)
        self._btn_run.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._btn_stop = self._button(btn_row, "■  Detener",
                                    COLORS["red"], self._stop_simulation,
                                    state="disabled")
        self._btn_stop.pack(side="left", fill="x", expand=True)

        self._btn_clear = self._button(card, "🗑  Limpiar",
                                    COLORS["surface2"], self._clear_all)
        self._btn_clear.pack(fill="x", pady=(4, 0))

    # ── Panel de métricas ────────────────────────────────────────────────────

    def _build_metrics_panel(self, parent):
        card = self._card(parent, "📊  Métricas")

        metrics = [
            ("Trabajos procesados",   "m_total",   "–"),
            ("Páginas impresas",      "m_pages",   "–"),
            ("Tiempo prom. espera",   "m_avg",     "–"),
            ("Mayor espera (job)",    "m_max_job", "–"),
            ("Mayor espera (seg)",    "m_max_t",   "–"),
            ("Tamaño máx. cola",      "m_qmax",    "–"),
            ("Tiempo simulado",       "m_dur",     "–"),
        ]
        self._metric_vars: dict[str, tk.StringVar] = {}
        for label, key, default in metrics:
            row = tk.Frame(card, bg=COLORS["surface"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=FONT_SMALL,
                    bg=COLORS["surface"], fg=COLORS["text_dim"],
                    width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            self._metric_vars[key] = var
            tk.Label(row, textvariable=var, font=FONT_BOLD,
                    bg=COLORS["surface"], fg=COLORS["text"],
                    anchor="e").pack(side="right")

    # ── Cola visual ──────────────────────────────────────────────────────────

    def _build_queue_visual(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="x", pady=(0, 8))

        tk.Label(frame, text="🖨  Impresora", font=FONT_BOLD,
                bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(side="left")

        self._printer_label = tk.Label(
            frame, text="[ LIBRE ]", font=FONT_MONO,
            bg=COLORS["surface2"], fg=COLORS["green"],
            relief="flat", padx=10, pady=4)
        self._printer_label.pack(side="left", padx=8)

        tk.Label(frame, text="  Cola →", font=FONT_BOLD,
                bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(side="left")

        # Canvas para la cola
        self._queue_canvas = tk.Canvas(
            frame, bg=COLORS["bg"], height=36,
            highlightthickness=0)
        self._queue_canvas.pack(side="left", fill="x", expand=True)
        self._queue_items: list[str] = []   # etiquetas de los trabajos en cola

    # ── Panel de log ─────────────────────────────────────────────────────────

    def _build_log_panel(self, parent):
        tk.Label(parent, text="📋  Registro de Eventos",
                font=FONT_BOLD, bg=COLORS["bg"],
                fg=COLORS["text_dim"]).pack(anchor="w")

        frame = tk.Frame(parent, bg=COLORS["surface"],
                        relief="flat", bd=0)
        frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            frame,
            font=FONT_MONO, bg=COLORS["surface"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", bd=8, state="disabled",
            wrap="none",
        )
        sb_v = ttk.Scrollbar(frame, orient="vertical",
                            command=self._log_text.yview)
        sb_h = ttk.Scrollbar(frame, orient="horizontal",
                            command=self._log_text.xview)
        self._log_text.configure(
            yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)

        sb_v.pack(side="right", fill="y")
        sb_h.pack(side="bottom", fill="x")
        self._log_text.pack(fill="both", expand=True)

        # Tags de color
        self._log_text.tag_config("arrival", foreground=COLORS["yellow"])
        self._log_text.tag_config("start",   foreground=COLORS["accent"])
        self._log_text.tag_config("finish",  foreground=COLORS["green"])
        self._log_text.tag_config("info",    foreground=COLORS["text_dim"])
        self._log_text.tag_config("metric",  foreground=COLORS["accent2"])

    # ──────────────────────────────────────────────────────────────────────────
    #  Helpers visuales
    # ──────────────────────────────────────────────────────────────────────────

    def _card(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=COLORS["surface"],
                        relief="flat", bd=1)
        outer.pack(fill="x", pady=(0, 12))
        tk.Label(outer, text=title, font=FONT_BOLD,
                bg=COLORS["surface"], fg=COLORS["text"],
                pady=6).pack(anchor="w", padx=10)
        ttk.Separator(outer).pack(fill="x")
        inner = tk.Frame(outer, bg=COLORS["surface"], padx=10, pady=8)
        inner.pack(fill="both")
        return inner

    def _button(self, parent, text, color, command, state="normal"):
        return tk.Button(
            parent, text=text, font=FONT_BOLD,
            bg=color, fg="white", activebackground=color,
            activeforeground="white", relief="flat", bd=0,
            padx=8, pady=6, cursor="hand2",
            command=command, state=state,
        )

    def _apply_ttk_theme(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Vertical.TScrollbar",
                        background=COLORS["surface2"],
                        troughcolor=COLORS["surface"],
                        arrowcolor=COLORS["text_dim"],
                        borderwidth=0)
        style.configure("Horizontal.TScrollbar",
                        background=COLORS["surface2"],
                        troughcolor=COLORS["surface"],
                        arrowcolor=COLORS["text_dim"],
                        borderwidth=0)
        style.configure("TSeparator", background=COLORS["border"])

    # ──────────────────────────────────────────────────────────────────────────
    #  Lógica de simulación
    # ──────────────────────────────────────────────────────────────────────────

    def _start_simulation(self):
        if self._running:
            return
        try:
            cfg = self._read_config()
        except ValueError as e:
            messagebox.showerror("Error de configuración", str(e))
            return

        self._clear_all(keep_config=True)
        self._running = True
        self._btn_run.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._set_status("● Simulando…", COLORS["yellow"])

        self._log_write("info", f"Iniciando simulación: {cfg}\n")

        self._sim_thread = threading.Thread(
            target=self._run_simulation_thread, args=(cfg,), daemon=True)
        self._sim_thread.start()

    def _run_simulation_thread(self, cfg: dict):
        """Ejecutado en hilo secundario para no bloquear la UI."""
        PrintTask.reset_counter()
        tasks = generate_random_tasks(
            duration=cfg["duration"],
            arrival_probability=cfg["prob"],
            min_pages=cfg["min_pages"],
            max_pages=cfg["max_pages"],
            seed=cfg["seed"],
        )
        self._events.append(("log", "info",
                            f"Trabajos generados: {len(tasks)}\n"))

        sim = PrintSimulation(
            tasks=tasks,
            pages_per_minute=cfg["ppm"],
            callback=self._on_sim_event,
        )
        result = sim.run()

        if self._running:
            self._events.append(("done", result))
        self._running = False

    def _on_sim_event(self, event_type: str, data: dict):
        """Llamado desde el hilo de simulación; solo encola eventos."""
        if not self._running:
            return
        self._events.append(("sim_event", event_type, data))

    def _stop_simulation(self):
        self._running = False
        self._set_status("● Detenido", COLORS["red"])
        self._btn_run.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._log_write("info", "\n⛔  Simulación detenida por el usuario.\n")

    # ──────────────────────────────────────────────────────────────────────────
    #  Polling de eventos (main thread)
    # ──────────────────────────────────────────────────────────────────────────

    def _poll_events(self):
        # Procesar hasta 30 eventos por tick para no saturar la UI
        for _ in range(30):
            if not self._events:
                break
            ev = self._events.pop(0)

            if ev[0] == "log":
                self._log_write(ev[1], ev[2])

            elif ev[0] == "sim_event":
                self._handle_sim_event(ev[1], ev[2])

            elif ev[0] == "done":
                self._on_simulation_done(ev[1])

        self.after(80, self._poll_events)

    def _handle_sim_event(self, event_type: str, data: dict):
        t = data["time"]
        task: PrintTask = data["task"]

        if event_type == "arrival":
            qs = data["queue_size"]
            msg = (f"t={t:>6}s  [LLEGADA]  Trabajo #{task.job_id} "
                f"({task.pages} pág.)  →  cola: {qs}\n")
            self._log_write("arrival", msg)
            self._queue_add(f"#{task.job_id}")

        elif event_type == "start":
            msg = (f"t={t:>6}s  [INICIO]   Impresora toma "
                f"Trabajo #{task.job_id} ({task.pages} pág.)\n")
            self._log_write("start", msg)
            self._queue_remove_first()
            self._printer_label.config(
                text=f"[ #{task.job_id} | {task.pages}p ]",
                fg=COLORS["accent"])

        elif event_type == "finish":
            msg = (f"t={t:>6}s  [FIN]      Trabajo #{task.job_id} "
                f"terminado.  Espera: {task.wait_time} s\n")
            self._log_write("finish", msg)
            self._printer_label.config(text="[ LIBRE ]",
                                    fg=COLORS["green"])

    def _on_simulation_done(self, result):
        self._btn_run.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._set_status("● Completado", COLORS["green"])

        mw = result.max_wait_task
        self._metric_vars["m_total"].set(str(result.total_jobs))
        self._metric_vars["m_pages"].set(str(result.total_pages_printed))
        self._metric_vars["m_avg"].set(f"{result.average_wait_time:.2f} s")
        self._metric_vars["m_max_job"].set(
            f"#{mw.job_id}" if mw else "–")
        self._metric_vars["m_max_t"].set(
            f"{mw.wait_time} s" if mw else "–")
        self._metric_vars["m_qmax"].set(str(result.max_queue_size))
        self._metric_vars["m_dur"].set(f"{result.total_seconds} s")

        self._log_write("metric", "\n" + result.summary() + "\n")

    # ──────────────────────────────────────────────────────────────────────────
    #  Visualización de la cola
    # ──────────────────────────────────────────────────────────────────────────

    def _queue_add(self, label: str):
        self._queue_items.append(label)
        self._redraw_queue()

    def _queue_remove_first(self):
        if self._queue_items:
            self._queue_items.pop(0)
        self._redraw_queue()

    def _redraw_queue(self):
        c = self._queue_canvas
        c.delete("all")
        x = 4
        for label in self._queue_items[:18]:   # mostrar máx. 18 cajas
            w = max(44, len(label) * 7 + 12)
            c.create_rectangle(x, 4, x + w, 32,
                                fill=COLORS["surface2"],
                                outline=COLORS["accent"], width=1)
            c.create_text(x + w // 2, 18, text=label,
                        font=FONT_SMALL, fill=COLORS["text"])
            x += w + 4
        if len(self._queue_items) > 18:
            c.create_text(x + 16, 18,
                        text=f"+{len(self._queue_items) - 18}",
                        font=FONT_SMALL, fill=COLORS["text_dim"])

    # ──────────────────────────────────────────────────────────────────────────
    #  Log
    # ──────────────────────────────────────────────────────────────────────────

    def _log_write(self, tag: str, text: str):
        self._log_text.config(state="normal")
        self._log_text.insert("end", text, tag)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    # ──────────────────────────────────────────────────────────────────────────
    #  Utilidades
    # ──────────────────────────────────────────────────────────────────────────

    def _read_config(self) -> dict:
        def get_float(key, lo, hi):
            try:
                v = float(self._cfg_vars[key].get())
            except ValueError:
                raise ValueError(f"'{key}' debe ser un número.")
            if not (lo <= v <= hi):
                raise ValueError(f"'{key}' debe estar entre {lo} y {hi}.")
            return v

        def get_int(key, lo, hi=None):
            try:
                v = int(self._cfg_vars[key].get())
            except ValueError:
                raise ValueError(f"'{key}' debe ser un entero.")
            if v < lo:
                raise ValueError(f"'{key}' debe ser ≥ {lo}.")
            if hi and v > hi:
                raise ValueError(f"'{key}' debe ser ≤ {hi}.")
            return v

        dur     = get_int("duration", 1)
        prob    = get_float("prob", 0.001, 1.0)
        min_p   = get_int("min_pages", 1)
        max_p   = get_int("max_pages", 1)
        ppm     = get_int("ppm", 1)
        seed    = get_int("seed", 0)

        if min_p > max_p:
            raise ValueError("Páginas mín. no puede ser mayor que páginas máx.")

        return dict(duration=dur, prob=prob,
                    min_pages=min_p, max_pages=max_p,
                    ppm=ppm, seed=seed)

    def _set_status(self, text: str, color: str):
        self._status_label.config(text=text, fg=color)

    def _clear_all(self, keep_config=False):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")
        for var in self._metric_vars.values():
            var.set("–")
        self._queue_items.clear()
        self._redraw_queue()
        self._printer_label.config(text="[ LIBRE ]", fg=COLORS["green"])
        self._set_status("● Listo", COLORS["green"])
        self._events.clear()


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = PrintQueueApp()
    app.mainloop()

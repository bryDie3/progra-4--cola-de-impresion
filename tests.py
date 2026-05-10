"""
tests.py – Pruebas unitarias para la simulación de cola de impresión.
Ejecutar con: python tests.py
"""

import unittest
from queue_ds import Queue
from models import PrintTask, Printer, generate_random_tasks
from simulation import PrintSimulation


# ═════════════════════════════════════════════════════════════════════════════
#  Tests de Queue
# ═════════════════════════════════════════════════════════════════════════════

class TestQueue(unittest.TestCase):

    def test_empty_queue(self):
        q = Queue()
        self.assertTrue(q.is_empty())
        self.assertEqual(len(q), 0)

    def test_enqueue_increases_size(self):
        q = Queue()
        q.enqueue("a")
        q.enqueue("b")
        self.assertEqual(q.size(), 2)

    def test_fifo_order(self):
        """El primer elemento en entrar debe ser el primero en salir."""
        q = Queue()
        for val in [10, 20, 30, 40]:
            q.enqueue(val)
        results = []
        while not q.is_empty():
            results.append(q.dequeue())
        self.assertEqual(results, [10, 20, 30, 40])

    def test_dequeue_empty_raises(self):
        q = Queue()
        with self.assertRaises(IndexError):
            q.dequeue()

    def test_peek_does_not_remove(self):
        q = Queue()
        q.enqueue(99)
        self.assertEqual(q.peek(), 99)
        self.assertEqual(q.size(), 1)

    def test_peek_empty_raises(self):
        q = Queue()
        with self.assertRaises(IndexError):
            q.peek()

    def test_single_element(self):
        q = Queue()
        q.enqueue("solo")
        self.assertEqual(q.dequeue(), "solo")
        self.assertTrue(q.is_empty())

    def test_repr(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        self.assertIn("Queue", repr(q))


# ═════════════════════════════════════════════════════════════════════════════
#  Tests de PrintTask
# ═════════════════════════════════════════════════════════════════════════════

class TestPrintTask(unittest.TestCase):

    def setUp(self):
        PrintTask.reset_counter()

    def test_valid_task(self):
        t = PrintTask(pages=5, arrival_time=10)
        self.assertEqual(t.pages, 5)
        self.assertEqual(t.arrival_time, 10)

    def test_invalid_pages_zero(self):
        with self.assertRaises(ValueError):
            PrintTask(pages=0, arrival_time=0)

    def test_invalid_pages_negative(self):
        with self.assertRaises(ValueError):
            PrintTask(pages=-3, arrival_time=0)

    def test_invalid_arrival_negative(self):
        with self.assertRaises(ValueError):
            PrintTask(pages=5, arrival_time=-1)

    def test_wait_time_before_start(self):
        t = PrintTask(pages=5, arrival_time=10)
        self.assertIsNone(t.wait_time)

    def test_wait_time_after_start(self):
        t = PrintTask(pages=5, arrival_time=10)
        t.start_time = 15
        self.assertEqual(t.wait_time, 5)

    def test_auto_id(self):
        t1 = PrintTask(pages=1, arrival_time=0)
        t2 = PrintTask(pages=1, arrival_time=0)
        self.assertNotEqual(t1.job_id, t2.job_id)


# ═════════════════════════════════════════════════════════════════════════════
#  Tests de Printer
# ═════════════════════════════════════════════════════════════════════════════

class TestPrinter(unittest.TestCase):

    def setUp(self):
        PrintTask.reset_counter()

    def test_initially_free(self):
        p = Printer(pages_per_minute=10)
        self.assertFalse(p.is_busy())

    def test_invalid_speed(self):
        with self.assertRaises(ValueError):
            Printer(pages_per_minute=0)

    def test_starts_task_marks_busy(self):
        p = Printer(pages_per_minute=60)   # 1 pág/s
        t = PrintTask(pages=3, arrival_time=0)
        p.start_task(t, current_time=0)
        self.assertTrue(p.is_busy())

    def test_double_start_raises(self):
        p = Printer(pages_per_minute=60)
        t1 = PrintTask(pages=1, arrival_time=0)
        t2 = PrintTask(pages=1, arrival_time=0)
        p.start_task(t1, 0)
        with self.assertRaises(RuntimeError):
            p.start_task(t2, 0)

    def test_tick_finishes_task(self):
        p = Printer(pages_per_minute=60)   # 1 página por segundo
        t = PrintTask(pages=1, arrival_time=0)
        p.start_task(t, current_time=0)
        result = p.tick(current_time=1)
        self.assertIsNotNone(result)
        self.assertFalse(p.is_busy())
        self.assertEqual(result.finish_time, 1)

    def test_tick_not_finished_yet(self):
        p = Printer(pages_per_minute=60)   # 1 página/segundo
        t = PrintTask(pages=5, arrival_time=0)
        p.start_task(t, current_time=0)
        for i in range(1, 5):
            result = p.tick(i)
            self.assertIsNone(result)
        result = p.tick(5)
        self.assertIsNotNone(result)


# ═════════════════════════════════════════════════════════════════════════════
#  Tests de Simulación
# ═════════════════════════════════════════════════════════════════════════════

class TestSimulation(unittest.TestCase):

    def setUp(self):
        PrintTask.reset_counter()

    def test_empty_simulation(self):
        sim = PrintSimulation(tasks=[], pages_per_minute=10)
        result = sim.run()
        self.assertEqual(result.total_jobs, 0)
        self.assertEqual(result.average_wait_time, 0.0)
        self.assertIsNone(result.max_wait_task)
        self.assertEqual(result.max_queue_size, 0)

    def test_single_task_no_wait(self):
        """Un único trabajo no debería esperar."""
        t = PrintTask(pages=1, arrival_time=0)
        sim = PrintSimulation(tasks=[t], pages_per_minute=60)
        result = sim.run()
        self.assertEqual(result.total_jobs, 1)
        self.assertEqual(result.processed_tasks[0].wait_time, 0)

    def test_fifo_processing_order(self):
        """Los trabajos deben procesarse en orden de llegada."""
        PrintTask.reset_counter()
        tasks = [
            PrintTask(pages=1, arrival_time=0),
            PrintTask(pages=1, arrival_time=1),
            PrintTask(pages=1, arrival_time=2),
        ]
        sim = PrintSimulation(tasks=tasks, pages_per_minute=60)
        result = sim.run()
        ids = [t.job_id for t in result.processed_tasks]
        self.assertEqual(ids, sorted(ids))

    def test_queue_grows_when_printer_busy(self):
        """Cola debe crecer si la impresora está ocupada con trabajo largo."""
        PrintTask.reset_counter()
        tasks = [
            PrintTask(pages=60, arrival_time=0),   # 60 segundos a 60ppm
            PrintTask(pages=1, arrival_time=1),
            PrintTask(pages=1, arrival_time=2),
        ]
        sim = PrintSimulation(tasks=tasks, pages_per_minute=60)
        result = sim.run()
        self.assertGreater(result.max_queue_size, 1)
        self.assertEqual(result.total_jobs, 3)

    def test_metrics_basic(self):
        PrintTask.reset_counter()
        tasks = [
            PrintTask(pages=60, arrival_time=0),
            PrintTask(pages=1, arrival_time=1),
        ]
        sim = PrintSimulation(tasks=tasks, pages_per_minute=60)
        result = sim.run()
        self.assertGreater(result.average_wait_time, 0)
        self.assertIsNotNone(result.max_wait_task)

    def test_random_generation(self):
        tasks = generate_random_tasks(
            duration=3600,
            arrival_probability=0.05,
            min_pages=1,
            max_pages=10,
            seed=42,
        )
        self.assertGreater(len(tasks), 0)
        for t in tasks:
            self.assertGreater(t.pages, 0)
            self.assertGreaterEqual(t.arrival_time, 0)

    def test_total_pages_counted(self):
        PrintTask.reset_counter()
        tasks = [PrintTask(pages=5, arrival_time=0),
                PrintTask(pages=3, arrival_time=1)]
        sim = PrintSimulation(tasks=tasks, pages_per_minute=60)
        result = sim.run()
        self.assertEqual(result.total_pages_printed, 8)


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for cls in [TestQueue, TestPrintTask, TestPrinter, TestSimulation]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n Todas las pruebas pasaron correctamente.")
    else:
        print(f"\n  {len(result.failures)} fallo(s), "
            f"{len(result.errors)} error(es).")

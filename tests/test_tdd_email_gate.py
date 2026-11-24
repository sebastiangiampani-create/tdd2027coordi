"""Pruebas locales sin Google, Gmail ni envio de mensajes."""
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tdd_email_gate import asistentes_unicos, en_ventana
from tdd_email_dedupe import es_envio_exitoso

TZ = ZoneInfo("America/Argentina/Buenos_Aires")


class EnviosTDD(unittest.TestCase):
    def setUp(self):
        self.fecha = datetime(2026, 11, 24, tzinfo=TZ).date()
        self.filas = [[""] * 16, [""] * 16, [""] * 16, [""] * 16]
        self.filas[0][14], self.filas[0][15] = "Fecha", "Turno"
        for i, dni, fecha in [(1, "123", "24/11/2026"),
                              (2, "123", "24/11/2026"),
                              (3, "456", "23/11/2026")]:
            self.filas[i][1] = dni
            self.filas[i][14] = fecha
            self.filas[i][15] = "Mañana"

    def test_solo_fecha_hoy_y_dni_unico(self):
        self.assertEqual(asistentes_unicos(self.filas, self.fecha), 1)

    def test_sin_asistencia_fecha_distinta(self):
        self.assertEqual(asistentes_unicos(self.filas, self.fecha.replace(day=25)), 0)

    def test_horario_local(self):
        for hora, expected in [(18, False), (19, True), (20, True), (21, True), (22, False)]:
            with self.subTest(hora=hora):
                self.assertEqual(en_ventana(datetime(2026, 11, 24, hora, 0, tzinfo=TZ)), expected)

    def test_no_reenvia_smtp_confirmado(self):
        runs = [{"id": 101, "path": ".github/workflows/tdd-email-19.yml",
                 "status": "completed", "created_at": "2026-11-24T22:05:00Z"}]
        jobs = lambda _: [{"steps": [{"name": "Enviar informe por correo en CCO", "conclusion": "success"}]}]
        self.assertTrue(es_envio_exitoso(runs, self.fecha, 202, jobs))
        self.assertFalse(es_envio_exitoso(runs, self.fecha, 101, jobs))

    def test_success_sin_paso_smtp_no_equivale_a_envio(self):
        runs = [{"id": 101, "path": ".github/workflows/tdd-email-19.yml",
                 "status": "completed", "conclusion": "success", "created_at": "2026-11-24T22:05:00Z"}]
        jobs = lambda _: [{"steps": [{"name": "Enviar informe por correo en CCO", "conclusion": "skipped"}]}]
        self.assertFalse(es_envio_exitoso(runs, self.fecha, 202, jobs))


if __name__ == "__main__":
    unittest.main()

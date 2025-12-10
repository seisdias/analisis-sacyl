# tests/db/test_paciente.py

from .base import BaseDBTestCase


class TestPaciente(BaseDBTestCase):
    def test_save_and_get_patient(self):
        info = {
            "nombre": "Borja",
            "apellidos": "Alonso Tristán",
            "fecha_nacimiento": "1985-06-15",
            "sexo": "M",
            "numero_historia": "HIST-123",
        }
        self.paciente.save(info)

        row = self.paciente.get()
        self.assertIsNotNone(row)
        self.assertEqual(row["nombre"], "Borja")
        self.assertEqual(row["apellidos"], "Alonso Tristán")
        self.assertEqual(row["numero_historia"], "HIST-123")

    def test_save_overwrites_previous_patient(self):
        self.paciente.save(
            {
                "nombre": "Paciente1",
                "apellidos": "Uno",
                "fecha_nacimiento": "1990-01-01",
                "sexo": "M",
                "numero_historia": "H1",
            }
        )
        self.paciente.save(
            {
                "nombre": "Paciente2",
                "apellidos": "Dos",
                "fecha_nacimiento": "1995-02-02",
                "sexo": "F",
                "numero_historia": "H2",
            }
        )

        row = self.paciente.get()
        self.assertIsNotNone(row)
        self.assertEqual(row["nombre"], "Paciente2")
        self.assertEqual(row["numero_historia"], "H2")

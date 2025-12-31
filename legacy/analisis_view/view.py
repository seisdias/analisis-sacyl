# analisis_view/view.py
# -*- coding: utf-8 -*-

"""
Vista principal de análisis de laboratorio.

- Contiene un panel superior con datos del paciente.
- Contiene un Notebook con 4 pestañas:
    • Hematología (HematologyTab)
    • Bioquímica (BioquimicaTab)
    • Gasometría (GasometriaTab)
    • Orina (OrinaTab)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from tkinter import ttk  # type: ignore

from ranges_config import RangesManager  # type: ignore
from db_manager import HematologyDB      # sólo para tipado

from .hematology_tab import HematologyTab
from .bioquimica_tab import BioquimicaTab
from .gasometria_tab import GasometriaTab
from .orina_tab import OrinaTab

logger = logging.getLogger(__name__)


class AnalisisView(ttk.Frame):
    """
    Frame principal:

      - Panel superior con datos del paciente.
      - Notebook con pestañas por tipo de análisis.
    """

    def __init__(
        self,
        master,
        db: Optional[HematologyDB] = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.db: Optional[HematologyDB] = db
        self.ranges_manager: Optional[RangesManager] = ranges_manager

        # Panel de datos del paciente
        self.meta_frame = self._create_patient_frame()
        self.meta_frame.pack(fill="x", side="top")

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Pestañas
        self.tab_hema = HematologyTab(
            self.notebook,
            db=self.db,
            ranges_manager=self.ranges_manager,
        )
        self.notebook.add(self.tab_hema, text="Hematología")

        self.tab_bioq = BioquimicaTab(
            self.notebook,
            db=self.db,
            ranges_manager=self.ranges_manager,
        )
        self.notebook.add(self.tab_bioq, text="Bioquímica")

        self.tab_gaso = GasometriaTab(
            self.notebook,
            db=self.db,
        )
        self.notebook.add(self.tab_gaso, text="Gasometría")

        self.tab_orina = OrinaTab(
            self.notebook,
            db=self.db,
            ranges_manager=self.ranges_manager,
        )
        self.notebook.add(self.tab_orina, text="Orina")

        # Inicializamos panel de paciente
        self._update_patient_info()

    # ------------------------------------------------------------
    #   Panel de datos del paciente
    # ------------------------------------------------------------
    def _create_patient_frame(self) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self, text="Datos del paciente")

        self.meta_labels: Dict[str, ttk.Label] = {
            "paciente": ttk.Label(frame, text="Paciente: -"),
            "nhc": ttk.Label(frame, text="Nº historia: -"),
            "fnac": ttk.Label(frame, text="Fecha nac.: -"),
            "sexo": ttk.Label(frame, text="Sexo: -"),
        }

        for lbl in self.meta_labels.values():
            lbl.pack(side="left", padx=5, pady=2)

        return frame

    def _set_patient_info(self, patient: Optional[Dict[str, Any]]) -> None:
        if not patient:
            self.meta_labels["paciente"].configure(text="Paciente: -")
            self.meta_labels["nhc"].configure(text="Nº historia: -")
            self.meta_labels["fnac"].configure(text="Fecha nac.: -")
            self.meta_labels["sexo"].configure(text="Sexo: -")
            return

        nombre = patient.get("nombre") or ""
        apellidos = patient.get("apellidos") or ""
        paciente_txt = (nombre + " " + apellidos).strip() or "-"

        nhc = patient.get("numero_historia") or "-"
        fnac = patient.get("fecha_nacimiento") or "-"
        sexo = patient.get("sexo") or "-"

        self.meta_labels["paciente"].configure(text=f"Paciente: {paciente_txt}")
        self.meta_labels["nhc"].configure(text=f"Nº historia: {nhc}")
        self.meta_labels["fnac"].configure(text=f"Fecha nac.: {fnac}")
        self.meta_labels["sexo"].configure(text=f"Sexo: {sexo}")

    def _update_patient_info(self) -> None:
        """
        Consulta la BD para obtener los datos del paciente y actualiza el panel.
        """
        if self.db is None or not getattr(self.db, "is_open", False):
            self._set_patient_info(None)
            return

        patient: Optional[Dict[str, Any]] = None
        try:
            patient = self.db.get_patient()
        except Exception:
            logger.exception("Error obteniendo datos del paciente")
        self._set_patient_info(patient)

    # ------------------------------------------------------------
    #   API pública
    # ------------------------------------------------------------
    def set_db(self, db: HematologyDB) -> None:
        self.db = db
        self.tab_hema.set_db(db)
        self.tab_bioq.set_db(db)
        self.tab_gaso.set_db(db)
        self.tab_orina.set_db(db)
        self._update_patient_info()

    def set_ranges_manager(self, ranges_manager: RangesManager) -> None:
        self.ranges_manager = ranges_manager
        self.tab_hema.set_ranges_manager(ranges_manager)
        self.tab_bioq.set_ranges_manager(ranges_manager)
        self.tab_orina.set_ranges_manager(ranges_manager)

    def clear(self) -> None:
        """
        Limpia todas las pestañas y resetea el panel de datos del paciente.
        """
        self.tab_hema.clear()
        self.tab_bioq.clear()
        self.tab_gaso.clear()
        self.tab_orina.clear()

        self._set_patient_info(None)

    def refresh(self) -> None:
        """
        Recarga los datos desde la BD en todas las pestañas.
        """
        logger.debug("AnalisisView.refresh()")

        # Actualizamos datos del paciente
        self._update_patient_info()

        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        self.tab_hema.refresh()
        self.tab_bioq.refresh()
        self.tab_gaso.refresh()
        self.tab_orina.refresh()

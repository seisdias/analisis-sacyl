# analisis_view/view.py
# -*- coding: utf-8 -*-

"""
Vista principal de análisis de laboratorio.

- Contiene un panel superior de metadatos (fecha, nº petición, origen).
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

      - Panel superior con metadatos comunes (fecha, nº petición, origen).
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

        # Panel de metadatos
        self.meta_frame = self._create_meta_frame()
        self.meta_frame.pack(fill="x", side="top")

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Pestañas
        self.tab_hema = HematologyTab(
            self.notebook,
            db=self.db,
            ranges_manager=self.ranges_manager,
            metadata_callback=self._set_metadata_from_row,
        )
        self.notebook.add(self.tab_hema, text="Hematología")

        self.tab_bioq = BioquimicaTab(self.notebook, db=self.db)
        self.notebook.add(self.tab_bioq, text="Bioquímica")

        self.tab_gaso = GasometriaTab(self.notebook, db=self.db)
        self.notebook.add(self.tab_gaso, text="Gasometría")

        self.tab_orina = OrinaTab(self.notebook, db=self.db)
        self.notebook.add(self.tab_orina, text="Orina")

    # ------------------------------------------------------------
    #   Panel de metadatos
    # ------------------------------------------------------------
    def _create_meta_frame(self) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self, text="Datos del análisis")

        self.meta_labels: Dict[str, ttk.Label] = {
            "fecha": ttk.Label(frame, text="Fecha: -"),
            "peticion": ttk.Label(frame, text="Nº petición: -"),
            "origen": ttk.Label(frame, text="Origen: -"),
        }

        for lbl in self.meta_labels.values():
            lbl.pack(side="left", padx=5, pady=2)

        return frame

    def _set_metadata_from_row(self, row: Dict[str, Any]) -> None:
        fecha = row.get("fecha_extraccion") or "-"
        peticion = row.get("numero_peticion") or "-"
        origen = row.get("origen") or "-"

        self.meta_labels["fecha"].configure(text=f"Fecha: {fecha}")
        self.meta_labels["peticion"].configure(text=f"Nº petición: {peticion}")
        self.meta_labels["origen"].configure(text=f"Origen: {origen}")

    # ------------------------------------------------------------
    #   API pública
    # ------------------------------------------------------------
    def set_db(self, db: HematologyDB) -> None:
        self.db = db
        self.tab_hema.set_db(db)
        self.tab_bioq.set_db(db)
        self.tab_gaso.set_db(db)
        self.tab_orina.set_db(db)

    def set_ranges_manager(self, ranges_manager: RangesManager) -> None:
        self.ranges_manager = ranges_manager
        self.tab_hema.set_ranges_manager(ranges_manager)

    def clear(self) -> None:
        """
        Limpia todas las pestañas y resetea el panel de metadatos.
        """
        self.tab_hema.clear()
        self.tab_bioq.clear()
        self.tab_gaso.clear()
        self.tab_orina.clear()

        self._set_metadata_from_row(
            {
                "fecha_extraccion": "-",
                "numero_peticion": "-",
                "origen": "-",
            }
        )

    def refresh(self) -> None:
        """
        Recarga los datos desde la BD en todas las pestañas.
        """
        logger.debug("AnalisisView.refresh()")

        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        self.tab_hema.refresh()
        self.tab_bioq.refresh()
        self.tab_gaso.refresh()
        self.tab_orina.refresh()

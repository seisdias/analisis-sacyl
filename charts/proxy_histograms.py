# charts/proxy_histograms.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Dict, Any, List, Optional


def _gaussian(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.0
    z = (x - mu) / sigma
    return exp(-0.5 * z * z)


def _safe_float(v) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def rbc_size_distribution_proxy(
    *,
    vcm: Optional[float],
    rdw: Optional[float],
    x_min: float = 50.0,
    x_max: float = 130.0,
    step: float = 1.0,
) -> Dict[str, Any]:
    """
    Histograma proxy de distribución de tamaño eritrocitario (RBC).
    - mu aproximado: VCM (fL)
    - sigma aproximado: derivado de RDW (%). Esto NO replica bins reales.
    Salida:
      - x: lista de fL
      - y: densidad (a.u.), normalizada a max=1
      - markers: mu y banda aproximada ligada a RDW
    """
    mu = _safe_float(vcm)
    rdw_pct = _safe_float(rdw)

    # Guardas: sin datos suficientes
    if mu is None:
        return {
            "ok": False,
            "reason": "Falta VCM (vcm) para el proxy RBC",
            "x": [],
            "y": [],
            "markers": [],
        }

    # sigma: aproximación visual. RDW suele ser % de variación.
    # Aproximamos sigma ~ (RDW% * mu) / 100. Si falta RDW, sigma "suave" por defecto.
    if rdw_pct is None:
        sigma = max(3.0, mu * 0.06)  # ~6% del VCM como anchura visual conservadora
        band = None
    else:
        sigma = max(2.0, (rdw_pct * mu) / 100.0)
        # banda de dispersión aproximada: mu ± sigma (no es RDW real)
        band = (mu - sigma, mu + sigma)

    # Rango X: centrado en mu, pero acotado por [x_min, x_max]
    # Si mu cae fuera, aún damos rango fijo para evitar "cosas raras"
    xs: List[float] = []
    ys: List[float] = []

    x = x_min
    while x <= x_max + 1e-9:
        xs.append(round(x, 3))
        ys.append(_gaussian(x, mu, sigma))
        x += step

    # Normalizar (max=1) para "densidad a.u."
    m = max(ys) if ys else 0.0
    if m > 0:
        ys = [y / m for y in ys]

    markers: List[Dict[str, Any]] = [{"name": "VCM", "x": mu}]
    if band is not None:
        markers.append({"name": "RDW (proxy band)", "x0": band[0], "x1": band[1]})

    return {
        "ok": True,
        "x": xs,
        "y": ys,
        "markers": markers,
        "labels": {"x": "Volumen eritrocitario (fL) [proxy]", "y": "Densidad (a.u.)"},
        "meta": {
            "is_proxy": True,
            "note": "Proxy basado en VCM y RDW; no bins reales del analizador.",
            "mu_vcm": mu,
            "sigma_proxy": sigma,
        },
    }

def plt_size_distribution_proxy(
    *,
    vpm: Optional[float],
    plaquetas: Optional[float],
    x_min: float = 3.0,
    x_max: float = 20.0,
    step: float = 0.25,
) -> Dict[str, Any]:
    """
    Histograma proxy de distribución de tamaño plaquetario (PLT).
    - mu aproximado: VPM (fL)
    - sigma: heurístico visual (plaquetas no aporta forma real; se usa solo como meta)
    Salida:
      - x: lista de fL
      - y: densidad (a.u.), normalizada a max=1
      - markers: VPM y nota de PLT
    """
    mu = _safe_float(vpm)
    plt_count = _safe_float(plaquetas)

    if mu is None:
        return {
            "ok": False,
            "reason": "Falta VPM (vpm) para el proxy PLT",
            "x": [],
            "y": [],
            "markers": [],
        }

    # sigma visual: distribución plaquetaria suele ser más estrecha y asimétrica,
    # pero aquí usamos gaussiana como proxy defendible.
    # sigma base ~ 1.5 fL, ajustada suavemente por VPM (sin exagerar).
    sigma = max(0.9, min(3.0, mu * 0.18))

    xs: List[float] = []
    ys: List[float] = []

    x = x_min
    while x <= x_max + 1e-9:
        xs.append(round(x, 3))
        ys.append(_gaussian(x, mu, sigma))
        x += step

    m = max(ys) if ys else 0.0
    if m > 0:
        ys = [y / m for y in ys]

    markers: List[Dict[str, Any]] = [{"name": "VPM", "x": mu}]
    if plt_count is not None:
        markers.append({"name": "PLT (recuento)", "value": plt_count})

    return {
        "ok": True,
        "x": xs,
        "y": ys,
        "markers": markers,
        "labels": {"x": "Volumen plaquetario (fL) [proxy]", "y": "Densidad (a.u.)"},
        "meta": {
            "is_proxy": True,
            "note": "Proxy basado en VPM (forma) y PLT (solo contexto); no bins reales del analizador.",
            "mu_vpm": mu,
            "sigma_proxy": sigma,
            "plt_count": plt_count,
        },
    }

def wbc_differential_proxy(
    *,
    neutro_pct: Optional[float],
    linf_pct: Optional[float],
    mono_pct: Optional[float],
    eos_pct: Optional[float],
    baso_pct: Optional[float],
    neutro_abs: Optional[float],
    linf_abs: Optional[float],
    mono_abs: Optional[float],
    eos_abs: Optional[float],
    baso_abs: Optional[float],
) -> Dict[str, Any]:
    """
    Proxy visual del diferencial leucocitario:
    - NO es histograma; es un apilado por % (y abs como info adicional si existe).
    """
    # Normalizar entrada
    pct = {
        "Neutrófilos": _safe_float(neutro_pct),
        "Linfocitos": _safe_float(linf_pct),
        "Monocitos": _safe_float(mono_pct),
        "Eosinófilos": _safe_float(eos_pct),
        "Basófilos": _safe_float(baso_pct),
    }
    abs_ = {
        "Neutrófilos": _safe_float(neutro_abs),
        "Linfocitos": _safe_float(linf_abs),
        "Monocitos": _safe_float(mono_abs),
        "Eosinófilos": _safe_float(eos_abs),
        "Basófilos": _safe_float(baso_abs),
    }

    have_any_pct = any(v is not None for v in pct.values())
    have_any_abs = any(v is not None for v in abs_.values())

    if not have_any_pct and not have_any_abs:
        return {
            "ok": False,
            "reason": "Faltan datos de diferencial leucocitario (% o absolutos) para WBC proxy",
            "categories": [],
            "pct": [],
            "abs": [],
        }

    categories = list(pct.keys())

    # PCT: si hay algunos None, los ponemos a 0 para pintar sin romper
    pct_list = [float(pct[c] or 0.0) for c in categories]

    # Si hay porcentajes y la suma es razonable, podemos renormalizar a 100 para apilado
    s = sum(pct_list)
    renorm = False
    if have_any_pct and s > 0 and (s < 95 or s > 105):
        # renormalización suave a 100 para visual (no cambia el orden)
        pct_list = [(v * 100.0 / s) for v in pct_list]
        renorm = True

    abs_list = [abs_.get(c) for c in categories]

    return {
        "ok": True,
        "categories": categories,
        "pct": pct_list,
        "abs": abs_list,
        "labels": {"x": "Subpoblaciones", "y": "Porcentaje (%)"},
        "meta": {
            "is_proxy": True,
            "note": "Proxy del diferencial leucocitario: barras apiladas por porcentaje (no histograma).",
            "renormalized_pct": renorm,
            "has_abs": have_any_abs,
        },
    }

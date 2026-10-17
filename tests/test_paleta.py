# wall-e-robot/tests/test_paleta.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.nucleo.paleta: mapeo de fracción a color por umbral."""


import pytest

from app.nucleo.paleta import Paleta, color_por_umbral


@pytest.mark.parametrize(
    "fraccion, esperado",
    [
        (1.00, Paleta.DORADO),
        (0.75, Paleta.DORADO),
        (0.50, Paleta.NARANJA),
        (0.20, Paleta.ROJO),
        (0.05, Paleta.GRIS),
        (0.00, Paleta.GRIS),
    ],
)
def test_color_por_umbral_normal(fraccion, esperado):
    """invertido=False: los valores altos son DORADO (p. ej. batería)."""
    assert color_por_umbral(fraccion) == esperado


@pytest.mark.parametrize(
    "fraccion, esperado",
    [
        (1.00, Paleta.ROJO),
        (0.75, Paleta.ROJO),
        (0.50, Paleta.NARANJA),
        (0.20, Paleta.DORADO),
        (0.00, Paleta.GRIS),
    ],
)
def test_color_por_umbral_invertido(fraccion, esperado):
    """invertido=True: los valores altos son críticos (p. ej. consumo)."""
    assert color_por_umbral(fraccion, invertido=True) == esperado


@pytest.mark.parametrize(
    "fraccion, esperado",
    [
        (0.70, Paleta.NARANJA),   # exactamente 0.70 no supera el umbral
        (0.40, Paleta.ROJO),      # exactamente 0.40 no supera el umbral
        (0.10, Paleta.GRIS),      # exactamente 0.10 sigue siendo apagado
        (0.100001, Paleta.ROJO),  # apenas por encima del 0.10
        (0.700001, Paleta.DORADO),
    ],
)
def test_color_por_umbral_limites(fraccion, esperado):
    """Los umbrales son estrictos (>), así que el valor exacto cae a la banda baja."""
    assert color_por_umbral(fraccion) == esperado


def test_color_por_umbral_devuelve_hexadecimal():
    """El resultado es siempre un color '#rrggbb' de la paleta."""
    color = color_por_umbral(1.00, invertido=True)
    assert color == Paleta.ROJO
    assert isinstance(color, str) and color.startswith("#") and len(color) == 7

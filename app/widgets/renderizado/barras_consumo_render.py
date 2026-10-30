# wall-e-robot/app/widgets/renderizado/barras_consumo_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: 5 barras + barra base grande, con el estilo del diseño.


from ...nucleo.paleta import Paleta
from ...nucleo.disenio import Disenio
from .base_render import RenderizadorBase, rectangulo_redondeado
from .recoloreo import Recoloreo


class BarrasConsumoRenderer(RenderizadorBase):
    """Renderer de las barras de consumo apiladas (la base es la más grande)."""

    def __init__(self, widget, canvas, e):
        """e: Escala (unidades de diseño -> píxeles)."""
        super().__init__(canvas)
        self.widget = widget
        self.e = e

    def _caja_barra(self, i):
        """(x1, y1, x2, y2, radio) de la barra i (0 = base, 1..5 hacia arriba)."""
        x1, _, x2, y_base = Disenio.BARRAS_CAJA
        if i == 0:
            return (x1, y_base - Disenio.BARRA_BASE_ALTO, x2, y_base, 36)
        arriba = y_base - Disenio.BARRA_BASE_ALTO - 21 - Disenio.BARRA_ALTO
        y1 = arriba - (i - 1) * Disenio.BARRA_PASO
        return (x1, y1, x2, y1 + Disenio.BARRA_ALTO, 24)

    def dibujar(self):
        """Dibuja o actualiza las barras: las encendidas toman el color de estado."""
        e = self.e
        total = self.widget.TOTAL_BARRITAS
        encendidas = self.widget.barritas_encendidas
        color = self.widget.color

        for i in range(total):
            x1, y1, x2, y2, radio = self._caja_barra(i)
            self._primera_vez(
                f"barra_{i}",
                lambda x1=x1, y1=y1, x2=x2, y2=y2, r=radio:
                    rectangulo_redondeado(
                        self.canvas, e(x1), e(y1), e(x2), e(y2), e(r),
                        width=max(2, e(10))),
            )

        if not self._hay_cambio("estado", (encendidas, color)):
            return
        for i in range(total):
            encendida = i < encendidas
            self.canvas.itemconfig(
                self._ids[f"barra_{i}"],
                fill=color if encendida else Paleta.FONDO_WIDGET,
                outline=(Recoloreo.interpolar(color, "#000000", 0.62)
                         if encendida else Paleta.FONDO_CANVAS),
            )

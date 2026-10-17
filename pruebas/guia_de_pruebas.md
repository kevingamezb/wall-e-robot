# Wall-E · Guía de Pruebas (cómo operar y probar el sistema)


**Curso:** Programación III, Ingeniería Mecatrónica UMNG
**Fecha:** 13/09/2026
**Autor:** Kevin Gámez
**Descripción:** Guía práctica para operar las pruebas del proyecto. Va dirigida al compañero de equipo y a cualquiera que necesite ejecutar la app, flashear el ESP32 o probar los componentes reales por separado.

> **Regla de oro para probar:** primero se prueba cada pieza por separado (cajón de prueba o módulo aislado en el firmware) y solo después se integra. La interfaz se puede probar completa con el simulador, sin tocar hardware.

---

## 1. Qué hay en el repositorio (resumen operativo)

```
wall-e-robot/
├── app/            # App de escritorio (Python + Tkinter). Depende de Pillow (assets PNG).
├── firmware/       # Firmware del ESP32 (PlatformIO / C++). Librerías usadas se
│                   # descargan solas al compilar (ingresar a la red).
├── configuracion/  # JSON persistente (mapeo de teclas del control).
├── pruebas/        # Runner de cajones + esta guía.
├── platformio.ini  # Configuración del build del firmware.
└── requirements.txt # Dependencias de la app (Pillow).
```

Todas las pruebas del lado **PC** se ejecutan desde la raíz del repositorio
(la carpeta donde está `app/`), NO dentro de `app/`.

---

## 2. Requisitos

| Componente | Requisito | Notas |
|---|---|---|
| PC | Python 3.10 o superior con Tkinter | Requiere **Pillow** para los assets PNG: `pip install -r requirements.txt`. Para pruebas automatizadas (pytest): `pip install -r requirements-dev.txt`. |
| ADVERTENCIA DEL FIRMWARE | PlatformIO | En VS Code: instalar la extensión "PlatformIO IDE". O usar la CLI (ver §4). |

> Los ojos e íconos de la GUI usan assets PNG de `app/recursos/` (teñidos con la `Paleta`); si falta un PNG, se cae al dibujo procedural por código.

---

## 3. Pruebas del lado PC (sin hardware) — "Cajones de prueba"

Cada módulo trae su propio cajón de pruebas (bloque `if __name__ == "__main__"`): al ejecutarlo
imprime `Pruebas OK` si todo está bien. Se ejecutan desde la **raíz del repositorio**:

```powershell
python -m app.nucleo.estado
python -m app.nucleo.paleta
python -m app.comunicacion.conexion
python -m app.widgets.renderizado.base_render
python -m app.widgets.renderizado.carga_recursos
python -m app.widgets.logica.boton
python -m app.widgets.logica.deslizador
python -m app.widgets.logica.gamepad
python -m app.widgets.logica.ojos
python -m app.widgets.logica.icono_sistema
python -m app.widgets.logica.sol_bateria
python -m app.widgets.logica.barras_consumo
python -m app.widgets.logica.proximidad
python -m app.widgets.logica.navegacion
python -m app.widgets.logica.logger_widget
python -m app.widgets.logica.mapeo_teclado
python -m app.widgets.logica.control_teclado
python -m app.pantallas.pantalla_principal
python -m app.pantallas.modal_controles
```

> **Atajo:** para correr **todos** los cajones de una sola vez (los que no abren ventanas) existe el runner:
>
> ```powershell
> python pruebas/ejecutar_cajones.py
> ```
>
> Imprime `[OK]`/`[FALLA]` por módulo y termina con código de salida 0 si todo está verde
> (a la fecha: **17 cajones en verde**, incluye lógica y `base_render`, que cierra su ventana solo).

Qué revisa cada uno (resumen):

| Cajón | Prueba |
|---|---|
| `nucleo.estado` | `EstadoRobot`, `Modo`, `NivelLog`, `Logger` |
| `nucleo.paleta` | Colores centralizados y `color_por_umbral()` |
| `comunicacion.conexion` | Simulador, `ConexionOffline` y **el parseo tolerante del protocolo real** (campos nuevos, `null`, `navegacion`, `posiciones_servos`, `multi`, y la pérdida de conexión marcada sin romper la app) |
| `widgets.renderizado.base_render` | Helpers HUD (`scanlines`, `corchetes_hud`, `banda_gradiente`, `fulgor_radial`, `anillo_con_halo`, `borde_panel`, `rectangulo_redondeado`, `interpolar_color`) |
| `widgets.renderizado.carga_recursos` | Loader de assets PNG: carga, tinte con la `Paleta` (por canal alfa), escala conservando aspecto, espejo y caché; con Tk retirado genera PNG temporales |
| `widgets.logica.ojos` / `icono_sistema` | Prioridad de `ExpresionOjos` (incluye `ERROR`) y mapeo `TipoIcono` → asset (incluye los 3 niveles de conexión) |
| `widgets.logica.gamepad` | Direcciones del d-pad (`{"tipo":"motor",...}`), cuello, **reposo en un único `{"tipo":"multi",...}`**, que **sin conexión no envía nada** y que **reposo devuelve los deslizadores al centro** |
| `widgets.logica.mapeo_teclado` | Perfil de controles: defaults, persistencia JSON, conflictos una-tecla-una-acción |
| `widgets.logica.control_teclado` | El driver teclado->gamepad: auto-repetido de motores, pasos de ejes y discretas de un solo disparo |
| `widgets.logica.boton` / `deslizador` | Suscripción/avisos, hover, estados de color |
| demás `widgets.*` | Lógica de cada widget de la pantalla |

### 3.1 La GUI completa en modo simulado

```powershell
python -m app.main
```

- Arranca con **`SIMULADOR`** conectado (no requiere ESP32).
- Debe mostrarse la pantalla única con: Estado (columna central con 5 barras), Navegación
  (medidor de proximidad + maniobra), Ojos, Sol de batería, Consumo, Logger, Gamepad y botones
  **CONECTAR / DESCONECTAR**.
- El simulador genera datos que cambian solos (batería baja lentamente, distancia varía,
  log de prueba cada 10 s) y alertas (obstáculo cerca < 15 cm, batería baja < 0.25).
- Para cerrar: `Ctrl+C` en la terminal o cerrar la ventana.

> Si algo sale mal aquí, el problema es de la app; el hardware no tiene nada que ver.

### 3.2 Controles por teclado (mapeo estilo emulador)

El botón **CONTROLES** (cabecera de CONTROL MANUAL) abre la ventana de mapeo
de teclas, como configuran los emuladores de consola (PCSX2/Dolphin):

1. Hacer clic en la tecla de una acción → **"Presiona una tecla..."**.
2. Pulsar la tecla nueva: queda asignada al instante y se guarda.
3. `Esc` cancela la asignación; el botón **✕** limpia la acción; **RESTAURAR
   POR DEFECTO** vuelve al perfil de fábrica.

Comportamiento al usar el teclado en la pantalla principal:

| Acción | Al mantener pulsada la tecla |
|---|---|
| Flechas (avanzar/retroceder/girar) | El comando motor se re-emite (no muere por el timeout de seguridad del firmware) |
| Cuello / hombros (Q/A, W/S, E/D) | Avanza de a 5° cada ~120 ms; el rango lo clampa el deslizador |
| Reposo | Dispara **una sola vez** (ignora el auto-repetido del teclado) |

- El teclado funciona **mientras la ventana tiene foco** (como en un emulador);
  si el foco se va a otra ventana, el estado se limpia solo.
- El perfil se guarda en `configuracion/controles.json`. Teclas por defecto:
  flechas = movimiento; `Q/A` cuello; `W/S` hombro izquierdo; `E/D` hombro
  derecho; `R` reposo.

### 3.3 Apariencia: "Holograma Axiom + Wall-E"

- Tema de la GUI: **nave Axiom / Wall-E** — azul espacial de fondo,
  paneles con scanners y corchetes HUD en cian (glow de EVE), y el robot en
  dorado/naranja (botones, deslizadores, medidor de proximidad).
- **Regla de oro de pintado:** ningún color en hexadecimal fuera de
  `Paleta` (`app/nucleo/paleta.py`). Botones = placa metálica con borde y
  halo dorado al presionar; deslizadores con marcas de 0°/extremos y halo en
  el thumb; logger = terminal de la nave (`[ts] ▸ mensaje`, niveles con
  color); navegación con medidor de proximidad y retícula; batería como sol con rayos.
- No hay animaciones nuevas: solo los ojos, el medidor de proximidad, el fade de
  botones y el brillo al interactuar; el resto se dibuja **una sola vez**
  (dirty-check) para no recargar el ciclo.
- **Ojos e íconos usan assets PNG** de `app/recursos/` (los SVG del diseño exportados con fondo
  transparente). `carga_recursos.py` los tiñe con la `Paleta` y los cachea; si falta un PNG, el
  renderer cae al **dibujo procedural** de siempre (la GUI no se rompe). Requiere **Pillow**
  (`pip install -r requirements.txt`). Los ojos tienen 5 expresiones por prioridad
  `SIN_DATOS → ERROR → MANUAL → OBSTACULO → NORMAL`, y el ícono de conexión tiene 3 niveles
  (`conectividad_alta/media/baja`) derivados por la frescura del último estado recibido.

> Para revisar la estética en vivo: `python -m app.main` en el simulador.
> Para revisar el layout en frío: `python -m app.pantallas.pantalla_principal`.

---

## 3a. Pruebas automatizadas con pytest

El proyecto dispone de una **suite automatizada** en `tests/` (pytest) que complementa los cajones (`if __name__ == "__main__"`). Las pruebas se centran en lógica pura y **no arrancan** el robot ni abren TCP a menos que se simule.

### 3a.1 Instalar dependencias de desarrollo

```powershell
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` instala `-r requirements.txt` (Pillow) y añade `pytest>=8.0` y `pytest-cov>=5.0`. Las dependencias del firmware las gestiona PlatformIO.

> **Nota:** Las pruebas con Tkinter (`raiz_tk`) requieren display. Si no lo hay, se **omiten** automáticamente (`pytest.skip`).

### 3a.2 Ejecutar las pruebas

```powershell
python -m pytest
python -m pytest -v
python -m pytest tests/test_estado.py
python -m pytest tests/test_estado.py::test_logger_recorta_a_30_lineas
python -m pytest -k conexion
```

`pytest.ini`: `testpaths = tests`, `python_files = test_*.py`, `python_functions = test_*`, `addopts = -ra`.

### 3a.3 Cobertura de código

```powershell
python -m pytest --cov=app --cov-report=term-missing
python -m pytest --cov=app --cov-report=html
```

`.coveragerc`: `source = app`; excluye `pragma: no cover`, `raise NotImplementedError` y **bloques `if __name__ == ["__main__"]:`** para evitar distorsionar la métrica de producción.

**Limitaciones conocidas:**
- `app/main.py`: 0% (punto de entrada GUI).
- Renderizadores Tk (`app/widgets/renderizado/*`): parcialmente cubiertos (no se fuerzan rutas gráficas para evitar pruebas frágiles).
- `app/widgets/renderizado/recoloreo.py`: sin uso en producción (ver Observaciones pendientes).

### 3a.4 VS Code Test Explorer

`.vscode/settings.json` (versionado) configura: `python.testing.pytestEnabled = true`, `python.testing.unittestEnabled = false`, `python.testing.pytestArgs = ["tests"]`, `python.testing.autoTestDiscoverOnSaveEnabled = true`, `python.analysis.extraPaths = ["."]`.

**Nota:** el descubrimiento desde VS Code depende del entorno del editor y **no se asume probado** en este documento.

### 3a.5 ¿Por qué se conservan los 17 cajones junto a pytest?

- Diagnóstico rápido (`python -m app.algun.modulo`) y chequeo manual.
- Complementarios con la suite automatizada.
- Transición controlada. Atajo: `python pruebas/ejecutar_cajones.py` (devuelve 0 si todos verdes).

```powershell
python pruebas/ejecutar_cajones.py
```

### 3a.6 Estructura y limitaciones

**Estructura:**
```text
tests/
├── conftest.py                # Configuración común y fixtures
└── test_*.py                  # Pruebas por módulo
```

**`conftest.py`:**
- Añade la raíz del repositorio a `sys.path` para importar `app` sin instalarlo.
- Fixture `raiz_tk()`: crea Tk retirada, la destruye y **omite (`pytest.skip`)** si no hay display.
- Helpers ligeros para reutilizar preparación.

**Limitaciones GUI/headless:**
- Sin display: tests con `raiz_tk` se omiten (correcto para evitar flakiness).
- Renderizadores: no se fuerzan ramas de dibujo/animación complejas.
- `app/main.py`: no se ejecuta en tests (abriría ventana/ciclo Tk).

---

## 4. Pruebas del lado firmware: compilar y flashear el ESP32

Abrir la carpeta `firmware/` como proyecto PlatformIO.

**Opción A — VS Code (recomendada para la operación diaria):**
1. Abrir `firmware/` con VS Code y la extensión PlatformIO.
2. Botón **Build** (martillo) para compilar; botón **Upload and Monitor** para flashear y abrir el serial.

**Opción B — Línea de comandos:**

```powershell
# Compilar el firmware
pio run

# Compilar + grabar al ESP32 por USB
pio run -t upload

# Ver el monitor serial (velocidad 115200)
pio device monitor
```

> Si `pio` no está en el PATH, usar la ruta del entorno instalado, por ejemplo
> `C:\Users\<usuario>\.platformio\penv\Scripts\platformio.exe run`.

Al arrancar, el ESP32 imprime en el monitor algo así:

```
AP iniciada: SSID='WALL-E' IP=192.168.4.1
Servidor TCP listo en puerto 8080
MODULO servos    = activo
MODULO distancia = activo
MODULO bateria   = activo
MODULO motores   = activo
MODULO oled      = activo
Setup completo.
```

Esto es **la señal de que el firmware está vivo y de cuántos módulos están activos**.

---

## 5. Pruebas aisladas por componente (lo más importante para operar)

El firmware tiene un "interruptor" de prueba por módulo: variables que se ponen en **1** si el
módulo está cableado/activo en esta prueba, y en **0** si no. Se cambian a mano al final de
`firmware/include/config.h`:

```cpp
typedef struct {
    bool servos;     // 3 servos MG90S directos a GPIO (2 brazos + cuello)
    bool distancia;  // HC-SR04 fijo al frente (mide distancia, sin barrido)
    bool bateria;    // INA219 (voltaje/corriente)
    bool oled;       // SSD1306 0.96"
    bool motores;    // TB6612FNG, 2 motores CC (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, true, true, true, true };
```

**Configuración actual:** todos los módulos (`servos`, `distancia`, `bateria`, `oled`, `motores`) activos.

> **Pendiente de verificación en hardware:** `MODULOS` asume que **todos** los sensores y
> periféricos están cableados. Un módulo habilitado pero **sin conectar** no se detecta
> (p. ej. el HC-SR04 sin eco tras 40 ms devuelve `-1` → `null`, `obstaculoCercano()` queda en
> falso y `hayModuloInactivo()` permanece en falso). Es decir, **no enciende el LED rojo ni
> avisa en la GUI**: el robot avanza en recto sin evasión. Antes de confiar en el arranque,
> confirmar el cableado o poner en `false` los módulos que falten.

**Reglas de comportamiento:**

- Un módulo en **0** no se inicializa, no se mueve ni se lee, y **la GUI ve valores neutros**
  (batería 1.0, consumo 0.0, distancia sin lectura). Así el panel no grita alertas falsas
  por hardware que no está conectado.
- Los servos tienen su propio listado `SERVOS_ACTIVOS[]` (mismo orden que la app):
  `cuello, hombro_izquierdo, hombro_derecho`. El hardware trae 3 servos (cuello + 2 brazos);
  no hay servos de pulgar. Incluso con un servo en 0, la telemetría manda el ángulo que la GUI
  cree que se pidió.
- El **HC-SR04** va fijo y pegado al frente: no hay servo de barrido; solo
  mide la distancia al obstáculo que tenga delante.

### 5.1 Procedimiento genérico de prueba de un módulo

1. Conectar el ESP32 por USB al PC y tener el monitor serial abierto.
2. En `config.h`, poner en **1** solo el módulo que se va a probar (y en 0 los demás).
3. Compilar + grabar (`pio run -t upload`).
4. Conectar el PC a la red WiFi **WALL-E** (abierta por defecto; si se puso
   `WIFI_AP_CLAVE`, usar esa clave).
5. Lanzar la app: `python -m app.main` → **CONECTAR** → IP `192.168.4.1` (puerto por defecto).
6. Operar el control y comprobar: el componente responde y el monitor serial muestra los comandos.

### 5.2 Pruebas orientativas por módulo

| Módulo | Cómo probarlo | Qué se espera |
|---|---|---|
| **Servos** (flag `servos=1`) | Mover el deslizador del **cuello** y los **hombros** en la GUI; presionar **REPOSO**. | El cuello y los 2 brazos se mueven suaves (10°..170°). Serial: `Servo 'cuello' -> 30 grados.` |
| **Motores** (flag `motores=1`) | Mantener el d-pad en direcciones: **arriba / abajo / izquierda / derecha**. | Las 2 ruedas giran: adelante, atrás, y giro en el sitio (a ~70 % de PWM, por ser motores de 6 V). Serial: `Motor -> arriba`. Las velocidades suben/bajan con rampa (sin tirón). **Seguridad:** si en modo manual no llega un comando en ~2 s, los motores se detienen solos con log `SEGURIDAD` ("Sin comando del operador..."). |
| **Distancia** (flag `distancia=1`) | Poner la mano frente al sensor (fijo al frente) a < 15 cm. | Al acercar la mano aparece la **advertencia** en la GUI, el medidor de proximidad se llena, se enciende el LED **rojo** y sale el log `Obstáculo muy cerca: X.Xcm`. |
| **Batería** (flag `bateria=1`) | Mirar el Sol de batería y el consumo con el robot alimentado y en reposo/operando. | El nivel se calcula del voltaje medido por el INA219 y baja conforme se descarga la batería. Log crítico (rojo) y LED **rojo** si el nivel cae por debajo de 0.10 (< ~6,8 V). |
| **OLED** (flag `oled=1`) | Ninguna acción extra. | La pantalla 0.96" muestra BAT / DIS / MODO / CONECTADO. |
| **LEDs** (siempre) | Ninguna acción extra. | Amarillo encendido cuando todo está normal; rojo cuando hay advertencia, error **o algún módulo desactivado** (config incompleta). El verde de encendido va directo al riel de 5 V. |

> **IMPORTANTE — cables todavía sin confirmar:** los pines de `firmware/include/pines.h` y el
> sentido A/B de las ruedas del TB6612FNG son **propuesta de arranque**. Antes de la primera prueba
> de motores, verificar: qué rueda es A y cuál B (AIN1/AIN2 vs BIN1/BIN2) y que girar "arriba"
> mueve el robot hacia adelante. Si sale al revés, se canjea A↔B en `lib/motores/motores.cpp`.

### 5.3 Cableado resumido (según `pines.h`)

| Señal | Pin ESP32 |
|---|---|
| I2C SDA / SCL | 21 / 22 |
| HC-SR04 TRIG / ECHO | 17 / 16 (ECHO con divisor 1k/2k) |
| TB6612 PWMA / AIN1 / AIN2 (izq.) | 25 / 26 / 27 |
| TB6612 PWMB / BIN1 / BIN2 (der.) | 33 / 32 / 14 |
| TB6612 STBY | 4 (HIGH habilita) |
| Servo brazo izq. / brazo der. / cuello | 18 / 19 / 23 |
| LED rojo / amarillo | 13 / 2 |

- INA219 en dirección **0x40** y OLED en **0x3C** (sin puentes).
- Servos alimentados por un buck de 5 V; motores por el buck del TB6612 (`VM`); GND común con el ESP32.
- **Nunca** meter 5 V a un GPIO: el ECHO del HC-SR04 pasa por un divisor de 1 kΩ / 2 kΩ.

---

## 6. Conectar la app al ESP32 real

1. Encender el ESP32 (debe aparecer la red **WALL-E**).
2. PC → conectarse a esa red WiFi (abierta por defecto; clave en `secrets.h` si se configuró).
3. Abrir la app (`python -m app.main`).
4. Presionar **CONECTAR**, confirmar IP `192.168.4.1` y CONECTAR.
   - Si la IP no funciona, leer la IP real que imprimió el Serial del ESP32.
5. Al conectar: el indicador pasa de **SIN CONEXIÓN** a **conectado** y se ve en el estado.
6. Para volver al simulador: **DESCONECTAR** deja el panel sin conexión (no vuelve al simulador).

---

## 7. Actualización OTA del firmware (por WiFi)

El robot no necesita cables para actualizarse. Hay **dos vías** y ambas requieren
la PC conectada a la red **WALL-E** (`192.168.4.1`).

### 7.1 Antes de empezar: credenciales

Las claves (WiFi del AP y del portal OTA) viven en `firmware/include/secrets.h`,
que **no se versiona**. Si no existe, copiar la plantilla:

```powershell
Copy-Item firmware/include/secrets.example.h firmware/include/secrets.h
```

`OTA_USUARIO` / `OTA_CLAVE` protegen el portal (Basic Auth) y espota. **Con
`OTA_CLAVE` vacía el portal queda abierto** (válido solo con la red aislada del
robot).

### 7.2 Compilar y obtener el MD5

```powershell
pio run
```

Al terminar, `scripts/firmware_manifest.py` imprime la versión, el tamaño y el
**MD5** del `.bin`, y además escribe `firmware.bin.md5`:

```
===================== FIRMWARE OTA =====================
  Version : 1.0.0
  Binario : ...\.pio\build\esp32dev\firmware.bin
  Tamano  : 896832 bytes
  MD5     : 7c79d28030666c00dd16008e35826b09
```

Ese MD5 es el que se pega en el portal para verificar la integridad de la subida.

### 7.3 Vía A — Portal web (navegador)

1. Conectar la PC a la red **WALL-E**.
2. Abrir `http://192.168.4.1/`.
3. Pegar el MD5 en el campo **MD5** (recomendado; rechaza un `.bin` corrupto).
4. Elegir `.pio/build/esp32dev/firmware.bin` y pulsar **Actualizar**.
5. El ESP32 reinicia con la versión nueva y corre el self-test (§7.5).

### 7.4 Vía B — ArduinoOTA / espota (línea de comandos)

```powershell
pio run -t upload --upload-port 192.168.4.1 --upload-protocol espota --upload-flags=--auth=<OTA_CLAVE>
```

(o `espota.py -i 192.168.4.1 -a <OTA_CLAVE> -f .pio/build/esp32dev/firmware.bin`).
ArduinoOTA ya envía el MD5 por su cuenta.

### 7.5 Rollback: si la versión nueva no arranca

Cada versión subida por OTA arranca **pendiente de confirmación**. Al iniciar,
una **tarea de guardia** (independiente del `loop()`) espera hasta
`OTA_AUTOCONFIRMA_MS` (15 s) a que el self-test confirme:

- El self-test es **interno** (no depende de la app). Son **fatales** (revierten):
  el AP sin IP y el servidor TCP sin escuchar. Los módulos habilitados que no
  inicializan (p. ej. un sensor no conectado) se registran como **aviso** y **no**
  revierten: llegar al `loop()` ya implica que todos los `iniciar()` terminaron.
- El `loop()` confirma en su **primera** vuelta (prueba de que el código corre).

Si algo falla, el firmware se cuelga o queda a medias, el bootloader **revierte
solo a la versión anterior** (anti-ladrillo). La versión nueva solo queda "fija"
cuando el self-test pasa; hasta entonces la app reporta `ota_pendiente=true`.

### 7.6 Publicar una versión nueva

1. Subir `PROYECTO_VERSION` en `firmware/include/config.h`.
2. `pio run` y copiar el MD5.
3. Subir por la vía A o B.
4. La app muestra `version_firmware` y `ota_pendiente` en cada estado.

---

## 8. El protocolo en 30 segundos (para depurar)

Medio: **WiFi TCP**, el ESP32 es el **servidor** y la PC el cliente. JSON, **un mensaje por línea**
(termina en `\n`).

**PC → ESP32 (comandos):**
```json
{"tipo":"servo","servo":"cuello","angulo":30}
{"tipo":"modo","modo":"manual"}
{"tipo":"motor","direccion":"arriba"}
{"tipo":"multi","comandos":[{"tipo":"servo","servo":"cuello","angulo":10}]}
```

**ESP32 → PC (estado ampliado y logs):**
```json
{"tipo":"estado","bateria":0.83,"modo":"manual","hay_advertencia":true,"hay_error":false,
 "distancia_cm":12.3,"navegacion":"alto","consumo_watts":3.4,"conexion_activa":true,"cargando":false,
 "modulo_inactivo":false,"version_firmware":"1.0.0","ota_pendiente":false,
  "tiempo_restante_min":42,"posiciones_servos":{"cuello":0,"hombro_izquierdo":10,"hombro_derecho":0}}
{"tipo":"log","origen":"DISTANCIA","mensaje":"Obstáculo muy cerca: 8.0cm","nivel":"advertencia"}
```

Detalles útiles:
- `distancia_cm` y `tiempo_restante_min` pueden venir como **null** (sin lectura del sensor de
  distancia / sin estimación de batería). La app lo interpreta como "no tocar ese dato".
- `navegacion` es la maniobra decidida en automático (`recto`/`izquierda`/`derecha`/`alto`); un
  valor desconocido se ignora y se conserva el anterior.
- Límites físicos validados en el firmware (`LIMITES[]` en `lib/comunicacion`):
  cuello ±70°, hombros ±50°. La tabla aún incluye `pulgar_izquierdo`/`pulgar_derecho`
  (±22°) por compatibilidad, pero no tienen servo físico: `Servos::MAPA_SERVOS` solo
  mapea 3 nombres, así que una orden a un pulgar pasa la validación y luego se
  **ignora** (no mueve nada). Un ángulo fuera de rango se rechaza.
- El ESP32 envía un estado cada **~500 ms**; la GUI redibuja cada 60 ms.

---

## 9. Alertas (advertencia / error)

| Señal | Criterio actual (firmware) | Qué ves en la GUI |
|---|---|---|
| `hay_advertencia` | Sensor de distancia activo y distancia ≤ **15 cm** | Ícono de advertencia + log naranja `DISTANCIA` |
| `hay_error` | Batería activa y nivel < **0.10** | Ícono de error + log rojo `BATERIA` + ojos en **ERROR** (rojo) |
| `modulo_inactivo` | Algún flag de `MODULOS` en `0` (config incompleta) | Ícono de error (sin log). En el firmware, el LED **rojo** también queda fijo |

Los logs de alerta se emiten **solo al transicionar** (se posan mientras la alerta persiste), para
no llenar el Logger de repeticiones.

---

## 10. Solución de problemas (rápido)

| Síntoma | Causa probable / acción |
|---|---|
| `ModuleNotFoundError` al correr un cajón | Se ejecutó desde dentro de `app/`. Correr desde la **raíz** del repositorio. |
| `pio` no es un comando reconocido | Usar la ruta del entorno: `C:\Users\<usuario>\.platformio\penv\Scripts\platformio.exe` |
| Monitor serial no da la línea "AP iniciada..." | Bajar la velocidad del monitor a **115200**; revisar el puerto USB (Upload). |
| "No se pudo conectar" en la GUI | El PC no está en la red **WALL-E**, el ESP32 no arrancó, o la IP no es `192.168.4.1`. Revisar Serial. |
| La GUI no marca falso el hardware ausente | Un módulo en **0** reporta neutro; si algo alerta sin hardware, revisar que su flag esté en 0. |
| Un servo no se mueve | Verificar la alimentación de 5 V (buck) y el GND común, y que `servos` esté en 1 en `config.h`. |
| Los motores no giran | Revisar que `STBY` del TB6612 esté en HIGH y que `motores=1`. Ojo: si algún módulo está en 0, el LED **rojo** queda fijo (no el amarillo) — es normal. El amarillo solo confirma el setup cuando **todos** los módulos están activos. |
| Las ruedas giran al revés / invertidas | Intercambiar A↔B en `lib/motores/motores.cpp` y confirmar ruedas en `pines.h`. |
| OTA: el portal pide usuario/clave y no entro | Credenciales en `firmware/include/secrets.h` (`OTA_USUARIO`/`OTA_CLAVE`); si no hay archivo, se usan las de `secrets.example.h`. |
| OTA: subida rechazada (401) | `OTA_CLAVE` configurada: el navegador debe autenticarse en el portal antes de subir. |
| OTA: "error de actualización" al subir el `.bin` | MD5 mal pegado, `.bin` corrupto o de otro proyecto; el firmware **no** se cambia y sigue la versión anterior. |
| OTA: el robot volvió solo a la versión vieja | El self-test no confirmó a tiempo (`OTA_AUTOCONFIRMA_MS`, 15 s): el rollback nativo actuó. Revisar el Serial. |
| OTA: no aparece `http://192.168.4.1/` | El PC no está en la red WALL-E o `WIFI_AP_SSID` cambió. Revisar el Serial del ESP32. |
| WARNING "Ignore unknown configuration option `monitor_filter`" | Inofensivo: el pio local no reconoce esa clave opcional. Ignorar. |

---

## 11. Checklist de prueba (marcar cada ítem completado)

**Lado PC (sin hardware):**
- [ ] Todos los cajones de §3 imprimen `Pruebas OK`.
- [ ] `python -m app.main` abre la pantalla única en modo SIMULADOR.
- [ ] El gamepad sin conexión no emite comandos (overlay SIN CONEXIÓN visible).
- [ ] CONTROLES: asignar una tecla, limpiar una acción y restaurar por defecto; al cerrar, `configuracion/controles.json` refleja los cambios.
- [ ] Con el gamepad conectado al simulador, el teclado mueve el estado (flechas reproducen el comando motor; Q/A mueven el cuello; reposo dispara una vez).
- [ ] Ojos e íconos se dibujan con los **assets PNG** de `app/recursos/` (instalar Pillow); al desconectar, los ojos pasan a **SIN_DATOS** y el ícono de conexión refleja el nivel por frescura. Si faltara un PNG, se ve el dibujo procedural.

**Lado firmware aislado:**
- [ ] Firma con solo `servos=1`: deslizadores mueven el cuello y los hombros; REPOSO los centra.
- [ ] Solo `motores=1`: d-pad mueve las ruedas en las 4 direcciones.
- [ ] `distancia=1`: el HC-SR04 fijo detecta y la mano cerca (< 15 cm) dispara advertencia, llena el medidor de proximidad y enciende el LED rojo.
- [ ] La GUI conectada a `192.168.4.1` muestra el estado real (no neutro) de los módulos activos.

**Lado OTA (por WiFi):**
- [ ] `pio run` imprime versión + MD5 y genera `firmware.bin.md5`.
- [ ] El portal `http://192.168.4.1/` abre (pide credenciales si `OTA_CLAVE` no está vacía).
- [ ] Subir el `.bin` con su MD5 reinicia el robot con la versión nueva.
- [ ] Subir un MD5 incorrecto **no** cambia el firmware (muestra error).
- [ ] Tras una subida, el estado reporta `ota_pendiente=true` y luego se confirma solo (self-test OK) sin volver atrás.
- [ ] Si se fuerza un fallo en el self-test, el robot **revierte solo** a la versión anterior.
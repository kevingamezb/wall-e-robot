# Wall-E · Documento General del Proyecto

**Curso:** Programación III, Ingeniería Mecatrónica UMNG
**Fecha de este documento:** 13/09/2026
**Autor:** Kevin Gámez
**Equipo:** 1 persona principal (arquitectura y piezas complejas) + 1 compañero (piezas acotadas, framework Tkinter)

> **Propósito de este documento.** Es el punto único de referencia que **encapsula la filosofía** del proyecto
> (principios, arquitectura, decisiones tomadas), **refleja el estado real** del repositorio (no el planeado)
> y **lista lo que está pendiente** en este momento. Los demás `.md` del repositorio siguen existiendo como
> referencia detallada de cada tema; este documento resume, corrige lo desactualizado y traza qué sigue.

---

## 1. Qué es el proyecto

Un robot Wall-E con mínimo 6 servos articulados (cuello, hombros, pulgares, radar) capaz de:

- Moverse de forma autónoma evadiendo obstáculos y detectando huecos en el piso.
- Ser controlado manualmente desde una app de PC vía WiFi.
- Mostrar su estado (batería, modo, sensores) en una pantalla con estética inspirada en la película.
- Apagarse de forma segura y vigilar su propio consumo energético.

**Hardware:** ESP32 (WiFi integrado), driver PCA9685 para servos, fuente separada para servos,
INA219 para consumo real, OLED I2C 0.96", botón de apagado físico (relé/MOSFET).
**Software PC:** app Python con Tkinter (interfaz gráfica), particionada en lógica + renderer.
**Software ESP32:** firmware en C++ (PlatformIO).
**Comunicación:** WiFi/TCP, JSON una línea por mensaje.

---

## 2. Filosofía y principios de diseño (encapsulada)

Estos principios gobiernan **todas** las decisiones técnicas. Si una decisión contradice uno,
primero se discute el principio.

### 2.1 Los cuatro principios rectores

1. **Separación de responsabilidades por capas.** Cada pieza (dato, lógica visual, dibujo,
   comunicación) vive en su propio lugar y nunca conoce los detalles internos de las demás.
   Permite cambiar una pieza (framework gráfico, datos simulados → reales) sin reescribir el resto.
2. **Construir de adentro hacia afuera, probando cada pieza aislada.** Nunca se construye una
   pieza que dependa de otra que todavía no existe o no está probada. Cada módulo implementado
   trae su propio `if __name__ == "__main__"` como cajón de pruebas.
3. **El robot debe sobrevivir sin la app.** El modo automático (evasión, decisión de moverse)
   vive en el ESP32, no en el PC — el robot no puede depender de una conexión activa para no chocar.
4. **Diseñar para cambiar de opinión barato.** Colores centralizados en `Paleta`, umbrales como
   función reutilizable (`color_por_umbral()`), comandos como JSON simple en vez de un protocolo rígido.

### 2.2 Patrón recurrente: caja de datos + suscriptores

`EstadoRobot` es una **caja de datos compartida** (N a 1 a N): todo lo que produce información escribe
ahí, y todo lo que la consume lee de ahí, sin conocerse entre sí. Widgets interactivos (`Boton`,
`Deslizador`) y el `Logger` usan **callbacks/suscripción**: avisan activamente cuando algo cambia,
nunca hacen polling ni dependen de revisar condiciones "a mano".

### 2.3 Reglas de convivencia del código

1. Nadie escribe un color en hexadecimal fuera de `Paleta` — se agrega ahí primero, se discute.
2. Ningún widget importa la capa de comunicación directo — todo widget recibe un `EstadoRobot` ya armado.
3. Todo dato mostrado en pantalla debe existir como campo en `EstadoRobot` antes de dibujarlo.
4. Cambios a `EstadoRobot` o `Conexion` se avisan antes de hacerlos — son los contratos que comparte todo el equipo.
5. El ESP32 nunca importa lógica de interfaz — solo entiende JSON de entrada/salida.
6. Ninguna tarea periódica en el ESP32 usa `delay()` — todas usan `millis()` no bloqueante.
7. Los widgets lógicos **nunca importan tkinter**; solo los renderers lo usan.

### 2.4 Decisiones ya tomadas (no reabrir sin razón)

| Tema | Decisión |
|---|---|
| Framework gráfico | **Tkinter** (solo en los renderers) |
| Microcontrolador | **ESP32** |
| Íconos | **Recoloreo por código** sobre PNG con canal alpha (Pillow), no un PNG por estado |
| Modo automático | Vive en el **ESP32**, máquina de estados simple (`if/else`), sin IA |
| Transición auto/manual | **Histéresis asimétrica**: fácil entrar a manual, difícil salir (timeout 2000 ms, a calibrar) |
| Comunicación | WiFi/TCP, **JSON una por línea** (`\n`), ESP32 como servidor |
| Apagado | Corte físico de alimentación (relé/MOSFET), no sleep de software |

---

## 3. Arquitectura

### 3.1 Capas (lado PC)

```
┌─────────────────────────────────────────┐
│  4. PANTALLAS  (monitoreo, control)      │  ← armado de layouts (vacías en el repo actual)
├─────────────────────────────────────────┤
│  3. WIDGETS  lógica + renderer           │  ← logica/ SIN tkinter; renderizado/ CON tkinter
├─────────────────────────────────────────┤
│  2. MODELO DE DATOS  (EstadoRobot, ...)  │  ← nucleo/estado.py · nucleo/paleta.py
├─────────────────────────────────────────┤
│  1. COMUNICACIÓN  (Conexion/…Simulada)   │  ← comunicacion/conexion.py
└─────────────────────────────────────────┘
```

Regla de oro: **cada capa solo conoce la de abajo**. Dentro de la capa 3, cada widget se separa en
**lógica** (qué mostrar) y **renderer** (cómo dibujarlo). El renderer depende del widget lógico, nunca al revés.

### 3.2 Lado ESP32 (firmware)

El ESP32 hace tres cosas: (1) lee sensores, (2) mueve servos/motores, (3) recibe/envía JSON por WiFi.
Nunca conoce `EstadoRobot`, widgets ni Tkinter. `src/main.cpp` es el loop no bloqueante que coordina todo
(actualmente es solo una plantilla; ver sección 6).

### 3.3 Flujo de una vuelta de comunicación

1. ESP32 lee sensores → arma JSON `{"tipo":"estado", ...}` y lo envía cada ~500 ms (patrón `millis()`).
2. PC acumula bytes y, al aparecer `\n`, deserializa el JSON completo (buffer de línea media).
3. `tipo:"estado"` → escribe en `EstadoRobot`; `tipo:"log"` → `estado.logger.agregar_linea(...)`.
4. Los widgets leen `EstadoRobot` y se redibujan.
5. El usuario mueve un control → PC arma `{"tipo":"servo", ...}` y lo envía.
6. ESP32 valida servo + rango y lo aplica; con `{"tipo":"modo", ...}` cambia de modo.

---

## 4. Estado REAL del repositorio (actualizado)

> **Importante:** la estructura real difiere de la descrita en `estructura_archivos_clases.md`. Las
> diferencias se anotan al final. `app/` funge como paquete *namespace* (no hay `__init__.py`).

```
wall-e-robot/
├── app/                                  # App de escritorio (Python)
│   ├── nucleo/                           # ← docs la llamaban "core/"
│   │   ├── estado.py        ✅ hecho     # Modo, NivelLog, EntradaLog, Logger, PosicionServos, EstadoRobot
│   │   └── paleta.py        ✅ hecho     # Paleta, PROPORCION_AUREA, color_por_umbral()
│   ├── comunicacion/
│   │   └── conexion.py      ✅ hecho     # Conexion (ABC), Comunicacion (TCP/real), ComunicacionSimulada
│   ├── widgets/
│   │   ├── logica/
│   │   │   ├── boton.py     ✅ hecho     # Boton (suscripción + color por estado)
│   │   │   ├── deslizador.py ✅ hecho     # Deslizador + MovimientoDeslizador (rango + valido)
│   │   │   ├── sol_bateria.py   ⬜ vacío  # (docs: "sol_carga.py")
│   │   │   ├── barras_consumo.py ⬜ vacío
│   │   │   ├── ojos.py          ⬜ vacío
│   │   │   ├── icono_sistema.py ⬜ vacío
│   │   │   ├── radar.py         ⬜ vacío
│   │   │   ├── logger_widget.py ⬜ vacío
│   │   │   └── gamepad.py       ⬜ vacío
│   │   └── renderizado/              # ⬜ 10/10 vacíos
│   │       ├── recoloreo.py  ⬜ vacío # (helper único, sin lógica pareja)
│   │       └── *_render.py   ⬜ vacío # todos los renderers pendientes
│   ├── pantallas/
│   │   ├── monitoreo.py     ⬜ vacío
│   │   └── control_manual.py ⬜ vacío
│   ├── main.py              ⬜ vacío    # GUI aún no arranca
│   └── requirements.txt     ⬜ vacío    # falta declarar pillow, etc.
├── firmware/                            # ESP32 (PlatformIO)
│   ├── src/main.cpp         ⬜ plantilla # aún no usa lib/comunicacion ni WiFi/sensores
│   └── lib/comunicacion/
│       ├── comunicacion.h   ✅ hecho     # clase Comunicacion (servidor TCP + JSON)
│       └── comunicacion.cpp ✅ hecho     # buffer \n, validación de servos/límites, servo/modO
├── walle_demo.html                     # MOCKUP visual de la GUI (no es la app real)
└── *.md                                # documentación (incluido este documento)
```

Leyenda: ✅ implementado · ⬜ placeholder/por hacer.

### 4.1 Nombres reales vs. nombres de los documentos

| Concepto | Documentos originales | Código real (asumir estos) |
|---|---|---|
| Carpetas de la app | `core/`, `render_tkinter/` | `nucleo/`, `renderizado/` |
| Caja de datos | `RobotState` | `EstadoRobot` |
| Línea de log | `LogEntry` | `EntradaLog` |
| Logger | `agregar()` / `suscribir()` | `agregar_linea()` / `agregar_suscriptor()` |
| Comunicación | `ConexionRobot` + `ConexionReal`/`ConexionSimulada` | `Conexion` + `Comunicacion`/`ComunicacionSimulada` |
| Consumo máximo | `consumo_max_watts` | `max_consumo_watts` |
| Sol | `SolCarga` / `sol_carga.py` | `sol_bateria.py` (lógica aún vacía) |
| Slider | `slider.py` / `SliderVertical` | `deslizador.py` / `Deslizador` |
| Posición de ángulo | `distancia_obstaculo_cm` → `PosicionServos` | incluye `radar_us`; ojos comentados |
| Renderers | `*_renderer.py` | `*_render.py` |

**Regla a seguir de ahora en adelante:** los nombres del **código** son canónicos; cuando se editen los
documentos de referencia, deben usar estos nombres.

### 4.2 Firmware: qué cubre `lib/comunicacion`

- Servidor TCP: acepta 1 cliente a la vez, acumula bytes hasta `\n`, ignora `\r` y líneas vacías.
- Comandos entrantes: `servo` (valida nombre + rango con `LIMITES[]`) y `modo` (solo "automatico"/"manual").
- Envío: `enviarEstado(...)` y `enviarLog(...)` en JSON con `StaticJsonDocument<512>`.
- Los límites calibrados en firmware coinciden con los del mockup HTML: cuello ±70°, hombros ±50°, pulgares ±22°.

---

## 5. Protocolo de comunicación (resumen vigente)

Medio: **WiFi TCP**, ESP32 como **servidor**, JSON **una línea por mensaje** (`\n` delimita).

**ESP32 → PC:**
```json
{"tipo":"estado","bateria":0.66,"modo":"automatico","distancia_cm":37.5,"consumo_watts":4.2,"conexion_activa":true}
{"tipo":"log","origen":"SENSOR","mensaje":"Obstáculo a 8cm","nivel":"advertencia"}
```

**PC → ESP32:**
```json
{"tipo":"servo","servo":"cuello","angulo":30}
{"tipo":"modo","modo":"manual"}
```

Detalle, ejemplos de código y justificaciones (buffer de línea media, `setblocking(False)`, TCP como
flujo de bytes): ver [`protocolo_comunicacion_wifi_json.md`](protocolo_comunicacion_wifi_json.md).
Allí se documentó además el comando `{"tipo":"multi","comandos":[...]}` (aún **no implementado** en firmware).

---

## 6. Hoja de ruta y estado

Fases del plan de API gráfica, con su estado **al 13/09/2026**:

| Fase | Contenido | Estado |
|---|---|---|
| 1 · Estado | `EstadoRobot`, `Paleta`, `color_por_umbral`, Logger | ✅ **Hecho** (nucleo/) |
| 2 · Conexión | `Conexion` (ABC), `ComunicacionSimulada`, `Comunicacion` (TCP) | ✅ **Hecho** en el lado Python; falta integrar |
| 3 · Interfaz gráfica | Widgets lógicos + renderers + 2 pantallas + `main.py` | 🔶 **En curso**: 2/7 widgets lógicos; 0 renderers; 0 pantallas |
| 4 · Lectura de sensores | Primer contacto con hardware real (ESP32 → PC) | ⬜ Pendiente |
| 5 · Movimiento de servos/motores | GUI → ESP32 real, servos físicos | ⬜ Pendiente |
| 6 · Modo automático | Máquina de estados de evasión en ESP32 | ⬜ Pendiente |

**En paralelo (hardware/mecánico):** diseño 3D → cableado → integración → pulido. El software no se
bloquea por el hardware: la interfaz se termina aparte con `ComunicacionSimulada`.

---

## 7. Lo pendiente (priorizado)

### 7.1 Implementación (en orden sugerido)

1. **`requirements.txt`**: declarar dependencias (`pillow` para recoloreo). Hoy está vacío.
2. **Widgets lógicos restantes** (en orden del plan): `sol_bateria`, `barras_consumo`, `ojos`,
   `icono_sistema`, `radar`, `logger_widget`, y por último `gamepad` (composición).
   Cada uno con su cajón de pruebas como `boton.py`/`deslizador.py`.
3. **Renderers** (`renderizado/*.py`), empezando por `recoloreo.py` (helper con Pillow) y los renderers
   de los widgets ya lógicos (`boton_render`, `deslizador_render`).
4. **Pantallas**: `monitoreo.py` y `control_manual.py` (reutilizan los mismos widgets, no duplicar).
5. **`main.py`**: arranca Tkinter + conexión (simulada primero) + loop de actualización.
6. **Firmware `src/main.cpp`**: integrar `lib/comunicacion`, configurar credenciales WiFi, loop no
   bloqueante con `millis()`, envío periódico de estado (~500 ms).

### 7.2 Decisiones pendientes (del plan general / API gráfica)

1. **Cómo se actualiza `EstadoRobot`**: polling periódico vs. callback al llegar datos.
   Se puede posponer sin costo hasta la fase de sensores reales.
2. **Política de hilo principal de la GUI**: `recv()` en el hilo principal congelaría la interfaz; se
   resuelve con threading (el curso lo toca justo antes de la integración).
3. **Navegación entre pantallas** Monitoreo ↔ Control manual: ¿botón en GUI o el ESP32 avisando que
   entró a modo manual? ¿Qué widgets se comparten sin duplicar instancias?
4. **Servos de los "ojos"**: el hardware los marca opcional/recomendado; en `PosicionServos` están
   comentados con "Aún no se ha decidido".
5. **Cómo descubrir la IP del ESP32**: IP estática vs. dinámica; mientras tanto imprimirla en OLED/serial.
6. **`__init__.py`**: decidir si dejar `app/` como namespace package o declararlo explícito.

### 7.3 Calibraciones (valores de arranque, no definitivos)

| Parámetro | Valor inicial | Dónde |
|---|---|---|
| Timeout para salir de modo manual (histéresis) | 2000 ms | plan general §4.5 (aún no implementado) |
| Umbral "obstáculo cercano" (modo automático) | 15 cm | plan general §4.4 (aún no implementado) |
| Límites físicos de servos | cuello ±70°, hombros ±50°, pulgares ±22° | `comunicacion.cpp` `LIMITES[]` — verificar contra piezas reales |
| Buffer JSON firmware | `512` estado/log · `4096` entrada | `comunicacion.cpp` — crecer si el protocolo agrega campos |

### 7.4 Inconsistencias concretas detectadas (a corregir)

1. ✅ **RESUELTO (13/09/2026)** — `Comunicacion.actualizar_estado` guardaba `modo` como **string crudo**
   (`app/comunicacion/conexion.py`); ahora usa `Modo(mensaje["modo"])`, consistente con
   `ComunicacionSimulada` y con el contrato del enum.
2. El mensaje `estado` **no actualiza** `cargando`, `tiempo_restante_min`, `hay_error`,
   `hay_advertencia` ni `posiciones_servos`. O el protocolo agrega esos campos, o se documenta que
   hoy solo llegan por log/demás. `distancia_cm` tolera `null` en el protocolo, pero el controlador
   lo asigna directo sin manejar `None`.
3. **Firmware**: el comando `{"tipo":"multi",...}` está definido en el protocolo pero no tiene
   dispatcher en `procesarMensaje` (hoy `servo`/`modo` y "Tipo desconocido").
4. **`src/main.cpp`** sigue siendo la plantilla de PlatformIO (variable `myFunction`) — la clase
   `Comunicacion` está construida pero **no se usa** en ningún lado todavía.
5. Los documentos originales están desactualizados en nombres y estructura (ver §4.1). Este documento
   es el punto de referencia; al editar los otros, alinearlos.

---
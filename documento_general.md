# Wall-E · Documento General del Proyecto

**Curso:** Programación III, Ingeniería Mecatrónica UMNG
**Fecha de este documento:** 15/10/2026
**Autor:** Kevin Gámez
**Equipo:** 1 persona principal (arquitectura y piezas complejas) + 1 compañero (piezas acotadas, framework Tkinter)

> **Propósito de este documento.** Es el punto único de referencia que **encapsula la filosofía** del proyecto
> (principios, arquitectura, decisiones tomadas), **refleja el estado real** del repositorio (no el planeado)
> y **lista lo que está pendiente** en este momento. Los demás `.md` del repositorio siguen existiendo como
> referencia detallada de cada tema; este documento resume, corrige lo desactualizado y traza qué sigue.

---

## 1. Qué es el proyecto

Un robot Wall-E con servos articulados (cuello y 2 brazos) y sensor de distancia ultrasónico fijo, capaz de:

- Moverse de forma autónoma evadiendo obstáculos (navegación en `lib/auto`, corriendo en el ESP32).
- Ser controlado manualmente desde una app de PC vía WiFi.
- Mostrar su estado (batería, modo, sensores) en una pantalla con estética inspirada en la película.
- Apagarse de forma segura y vigilar su propio consumo energético.

**Hardware:** ESP32 (WiFi integrado), 3 servos MG90S conectados directo a GPIO con fuente aparte (buck de
5 V), driver TB6612FNG con 2 motores CC, INA219 para consumo real (dir. 0x40), OLED I2C 0.96" (dir. 0x3C),
HC-SR04 (sensor de distancia fijo al frente) y 2 LEDs indicadores (rojo/amarillo; el verde va al riel de 5 V).
**Software PC:** app Python con Tkinter (interfaz gráfica), particionada en lógica + renderer.
**Software ESP32:** firmware en C++ (PlatformIO), con pruebas aisladas por módulo (flags en `config.h`).
**Comunicación:** WiFi/TCP, JSON una línea por mensaje. El ESP32 actúa en **modo AP** (red `WALL-E`).

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
| Iconos | **Dibujados por código Tkinter** (sin Pillow ni PNG). `recoloreo.py` quedó vacío/sin usar |
| Pantalla final | **Una sola `PantallaPrincipal`** (se eliminaron `monitoreo.py` y `control_manual.py`) |
| Modo automático | Vive en el **ESP32**, máquina de estados simple (`if/else`), sin IA |
| Módulo autónomo | `lib/auto` **no tiene hardware propio**: usa los módulos globales `sensorDistancia` y `motores`. No lleva flag en `MODULOS`; se activa solo si `MODULOS.motores && MODULOS.distancia` |
| Transición auto/manual | **Histéresis asimétrica**: fácil entrar a manual, difícil salir (timeout 2000 ms, a calibrar) |
| Comunicación | WiFi/TCP, **JSON una por línea** (`\n`), ESP32 como **servidor en modo AP** (`WALL-E`, IP 192.168.4.1, puerto 8080) |
| Pruebas de hardware aisladas | Flags 0/1 `MODULOS` en `firmware/include/config.h`; módulo en 0 reporta **valores neutros** a la GUI |
| Apagado | Corte físico de alimentación (relé/MOSFET), no sleep de software |
| Look & feel | **"Holograma Axiom + Wall-E"**: azul espacial de fondo, scanlines y corchetes HUD en cian (EVE) en los paneles, robot en dorado/naranja; **brillo estático sutil**, sin animaciones nuevas (solo ojos, medidor de proximidad, fade de botones y brillo al interactuar) |
| Estructura de la pantalla | **Barra de sistema** superior (ENLACE · MODO · BATERÍA) + tarjetas con 4 **corchetes HUD** en las esquinas (que sobreviven al redimensionado); grilla fija: fila 1 ESTADO + TERMINAL, fila 2 NAVEGACIÓN + CONTROL MANUAL |

---

## 3. Arquitectura

### 3.1 Capas (lado PC)

```
┌─────────────────────────────────────────┐
│  4. PANTALLAS  (armado de layouts)       │  ← pantalla_principal.py (una sola pantalla)
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
Nunca conoce `EstadoRobot`, widgets ni Tkinter. Está dividido en **una librería por componente** alojada bajo
`lib/` y orquestada por `src/main.cpp`, un loop **no bloqueante** (`millis()`, sin `delay()`):

- `lib/comunicacion` — servidor TCP + JSON: comandos `servo`, `modo`, `motor`, `multi`; telemetría ampliada.
- `lib/servos` — 3 servos MG90S (ESP32Servo), nombre→servo físico, centro 0°→90° y clamp 10..170°.
- `lib/motores` — TB6612FNG diferencial (arriba/abajo/izquierda/derecha), PWM por ESP32PWM + STBY.
- `lib/distancia` — HC-SR04 no bloqueante (máquina de estados por `micros()`), sensor fijo al frente.
- `lib/bateria` — INA219 (0x40): nivel, corriente, watts, estimación de minutos.
- `lib/oled` — SSD1306 (0x3C): estado, batería, distancia y modo.
- `lib/leds` — 2 LEDs indicadores de estado (rojo = alerta, amarillo = funcionando).
- `lib/auto` — navegación autónoma (evita obstáculos). **No tiene hardware propio**: decide usando los
  módulos globales `sensorDistancia` y `motores`. API: `iniciar()`, `actualizar()`,
  `modoAutonomo(bool)`, `hayObstaculo()`, `navegacion()`.

Cada módulo **de hardware** se activa con su flag en `include/config.h`. Con el flag en **0**, el módulo no se
toca y la telemetría manda valores neutros (baterías 1.0, consumo 0.0, distancia `null`) para que la GUI no
grite alertas falsas por hardware ausente. Cómo operar estas pruebas: ver
[`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md).

`lib/auto` es el único sin flag propio, porque no toca pines: `main.cpp` lo arranca solo si
`MODULOS.motores && MODULOS.distancia`. **Hoy `MODULOS.distancia` está en `false`**, así que la
navegación autónoma arranca desactivada hasta que se cable el HC-SR04.

El orden del `loop()` importa y es:

1. `comunicacion.escucharCliente()` — llegan órdenes (cambian el modo).
2. Seguridad de manual: sin orden del operador por `TIEMPO_MANUAL_TIMEOUT_MS`, `motores.detener()`.
3. Sensores: `sensorDistancia.actualizar()` y, cada `LECTURA_BATERIA_MS`, `bateria.actualizarLectura()`.
4. `autoRobot.modoAutonomo(...)` — sincroniza el modo; al salir de automático detiene los motores.
5. `autoRobot.actualizar()` — decide y pide el movimiento.
6. `motores.actualizar()` — aplica la rampa hacia la velocidad pedida.
7. Telemetría cada `ENVIO_ESTADO_MS` (500 ms).

### 3.2.1 Cómo decide la navegación (`lib/auto`)

Máquina de estados de tres ramas, sin IA y sin `delay()`:

| Condición | Acción | `navegacion` reportada |
|---|---|---|
| Sin eco (`distanciaCm() < 0`) | `motores.detener()` — no se avanza a ciegas | `"alto"` |
| Obstáculo ≤ `UMBRAL_OBSTACULO_CM` (15 cm) | `motores.mover("derecha")` — giro en el sitio | `"derecha"` |
| Camino libre | `motores.mover("arriba")` | `"recto"` |
| Modo manual | no decide; los motores manda el operador | `"recto"` |

`hayObstaculo()` delega en `sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM)`, que **descarta
las lecturas sin eco**: si no, el `-1` del sensor cumpliría `-1 < 15` y el robot giraría en círculo
con el sensor caído. Solo actúa cuando el sensor avisa `hayLecturaNueva()` (ciclo de 250 ms).

### 3.3 Flujo de una vuelta de comunicación

1. ESP32 lee sensores → arma JSON `{"tipo":"estado", ...}` y lo envía cada **500 ms** (patrón `millis()`).
2. PC acumula bytes y, al aparecer `\n`, deserializa el JSON completo (buffer de línea media).
3. `tipo:"estado"` → escribe en `EstadoRobot` (parseo **tolerante**, campos faltantes/`null` no pisan valores);
   `tipo:"log"` → `estado.logger.agregar_linea(...)`.
4. Los widgets leen `EstadoRobot` y se redibujan.
5. El usuario mueve un control → PC arma `{"tipo":"servo"|"motor"|"modo"|"multi", ...}` y lo envía.
6. ESP32 valida servo + rango (`LIMITES[]`), modo o dirección y lo aplica sobre sus librerías de hardware.
7. En paralelo, `lib/auto` decide la maniobra del movimiento a partir del sensor de distancia cuando el
   modo es automático; esa decisión es la que viaja en el campo `navegacion` del siguiente estado.

### 3.4 Ojos e íconos: assets PNG teñidos con la Paleta

Los ojos y los íconos de sistema tienen ahora **assets** (diseñados en Inkscape, `app/recursos/*.svg`) y se
dibujan con **imágenes**, no con trazos hechos a mano. Tkinter no lee SVG, así que cada SVG se exporta a
**PNG con fondo transparente** y `carga_recursos.py` lo **tiñe con un color de la `Paleta`** (usando el canal
alfa), lo escala conservando aspecto y lo cachea como `PhotoImage`. Así el color sigue saliendo de un único
lugar (regla de oro de pintado). Si un PNG **no** está exportado, el renderer cae al **dibujo procedural** de
siempre (fallback), de modo que la GUI nunca se rompe por un asset ausente.

**Expresiones de ojos** (`ExpresionOjos`, una imagen por ojo; el derecho se dibuja espejado). Se evalúan en
este orden de prioridad:

| Prioridad | Expresión | Disparador | Asset | Color |
|---|---|---|---|---|
| 1 | `SIN_DATOS` | sin enlace | `ojo_desconectado` | gris |
| 2 | `ERROR` | `hay_error` (batería crítica) | `ojo_error` | rojo |
| 3 | `MANUAL` | modo manual | `ojo_manual` | naranja |
| 4 | `OBSTACULO` | obstáculo ≤ 15 cm | `ojo_obstaculo` | rojo |
| 5 | `NORMAL` | resto | `ojo_normal` | dorado |

**Íconos de sistema** (`TipoIcono` → asset): `ADVERTENCIA→advertencia`, `CARGANDO→cargando`,
`MODO_MANUAL→controlador`, `ERROR→error`, `CONEXION→conectividad_*`. El de conexión usa **tres niveles**
(`conectividad_alta/media/baja`) según `EstadoRobot.nivel_conexion`. Ese nivel **lo deriva la app** por la
**frescura** del último `estado` recibido (el firmware manda cada 500 ms): `alta` < 0.8 s, `media` < 2 s,
`baja` el resto, `nula` sin enlace (`conexion.py` `nivel_por_frescura()`). No viaja en el protocolo JSON.

---

## 4. Estado REAL del repositorio (actualizado)

```
wall-e-robot/
├── app/                                  # App de escritorio (Python). Paquete con __init__.py
│   ├── nucleo/
│   │   ├── estado.py        ✅ hecho     # Modo, Maniobra, NivelConexion, NivelLog, EntradaLog, Logger,
│   │   │                                 #   PosicionServos, EstadoRobot
│   │   └── paleta.py        ✅ hecho     # Paleta, PROPORCION_AUREA, color_por_umbral()
│   ├── comunicacion/
│   │   └── conexion.py      ✅ hecho     # Conexion (ABC), Comunicacion (TCP/real), ComunicacionSimulada,
│   │                                      # ConexionOffline, _procesar_mensaje() tolerante (protocolo ampliado)
│   ├── widgets/
│   │   ├── logica/          ✅ 12/12     # boton, deslizador, sol_bateria, barras_consumo, ojos, icono_sistema,
│   │   │                                 # proximidad, navegacion, logger_widget, gamepad, mapeo_teclado,
│   │   │                                 # control_teclado — TODOS con cajón de pruebas (sin tkinter)
│   │   └── renderizado/     ✅ 12/13     # *_render.py + base_render.py (helpers HUD: scanlines, corchetes_hud,
│   │   │                                 #   borde_panel, fulgor_radial, banda_gradiente, anillo_con_halo…)
│   │   │                                 #   + tarjeta.py (corchetes en las esquinas) + carga_recursos.py
│   │   │                                 #   (PNG de recursos: carga, tinte, escala y espejo). recoloreo.py ⬜ vacío
│   ├── pantallas/
│   │   ├── pantalla_principal.py ✅      # la única pantalla del sistema (monitoreo/control_manual eliminados);
│   │   │                                 #   barra de sistema (ENLACE/MODO/BATERÍA) + corchetes HUD
│   │   ├── modal_controles.py ✅         # modal de configuración de teclas del control manual
│   │   └── iconos/          ⬜ vacío      # los íconos reales viven en app/recursos/ (ver §3.4)
│   ├── recursos/            ✅ hecho     # 12 SVG + PNG exportados (ojos e íconos de sistema); los PNG se
│   │                                     #   tiñen con la Paleta al cargarse (ver §3.4)
│   ├── main.py              ✅ hecho      # arranca la GUI: SIMULADOR → CONECTAR(IP) → DESCONECTAR
│   └── (dependencia: Pillow — ver requirements.txt en la raíz)
├── firmware/                            # ESP32 (PlatformIO) — COMPILA (Flash ~62%, RAM ~14%)
│   ├── include/
│   │   ├── pines.h          ✅ hecho     # GPIO: I2C (INA219 0x40, OLED 0x3C), TB6612, 3 servos,
│   │   │                                 #   HC-SR04 (PIN_US_*) y LEDs. Ver esquema_de_conexion.md
│   │   └── config.h         ✅ hecho     # MODULOS (flags 0/1 de pruebas aisladas), AP WALL-E, umbrales y periodos
│   ├── src/main.cpp         ✅ hecho     # loop no bloqueante millis(); AP; Wire.begin; init de módulos por flag;
│   │                                     #   sincroniza modo con lib/auto; LEDs; telemetría 500 ms
│   └── lib/
│       ├── comunicacion/    ✅ hecho     # servidor TCP; servo/modo/motor/multi; enviarEstado() ampliado; modo()
│       ├── servos/          ✅ hecho     # 3 servos MG90S (ESP32Servo), nombre→servo físico, angulosUsuario()
│       ├── motores/         ✅ hecho     # TB6612FNG diferencial (arriba/abajo/izquierda/derecha), ESP32PWM + STBY
│       ├── distancia/       ✅ hecho     # HC-SR04 no bloqueante (sensor fijo al frente)
│       ├── bateria/         ✅ hecho     # INA219: nivel, corriente, watts, minutos restantes
│       ├── oled/            ✅ hecho     # SSD1306: estado, batería, distancia y modo
│       ├── leds/            ✅ hecho     # 2 LEDs indicadores (rojo alerta / amarillo funcionando)
│       └── auto/            ✅ hecho     # navegación autónoma (evita obstáculos); SIN hardware propio
├── configuracion/
│   └── controles.json      ✅ hecho     # mapeo persistente de teclas del control manual
├── pruebas/
│   ├── ejecutar_cajones.py  ✅ hecho     # corre los 17 cajones sin GUI y resume resultados
│   └── guia_de_pruebas.md   ✅ hecho     # cómo operar cajones, GUI simulado y pruebas aisladas de hardware
├── platformio.ini          ✅ hecho     # [platformio] apunta a firmware/{src,lib,include}; lib_deps
├── requirements.txt        ✅ hecho     # dependencia de la app: Pillow (assets PNG)
├── esquema_de_conexion.md  ✅ hecho     # cableado por componente (incluye alimentación y tierra común)
├── LICENSE
└── documento_general.md                  # este documento
```

Leyenda: ✅ implementado/presente · ⬜ placeholder/por hacer.

### 4.1 Nombres reales vs. nombres de los documentos

| Concepto | Documentos originales | Código real (asumir estos) |
|---|---|---|
| Carpetas de la app | `core/`, `render_tkinter/` | `nucleo/`, `renderizado/` |
| Caja de datos | `RobotState` | `EstadoRobot` |
| Línea de log | `LogEntry` | `EntradaLog` |
| Logger | `agregar()` / `suscribir()` | `agregar_linea()` / `agregar_suscriptor()` |
| Comunicación | `ConexionRobot` + `ConexionReal`/`ConexionSimulada` | `Conexion` + `Comunicacion`/`ComunicacionSimulada` + `ConexionOffline` |
| Consumo máximo | `consumo_max_watts` | `max_consumo_watts` |
| Slider | `slider.py` / `SliderVertical` | `deslizador.py` / `Deslizador` + `MovimientoDeslizador` |
| Posición de ángulo | `distancia_obstaculo_cm` → `PosicionServos` | ojos comentados |
| Sensor de distancia | `Radar` / `radar.py` / `radar_us` / pines `PIN_RADAR_*` | `SensorDistancia` / `proximidad.py` / campo `navegacion` / pines `PIN_US_*` |
| Navegación | (no existía) | `Maniobra` (enum) + `lib/auto`; tarjeta GUI **NAVEGACIÓN** |
| Expresión de ojos | (no existía) | `ExpresionOjos` (enum) + asset `ojo_<expresión>.png` (uno por ojo) |
| Nivel de conexión | (no existía) | `NivelConexion` (enum) derivado por frescura; assets `conectividad_alta/media/baja` |
| Renderers | `*_renderer.py` | `*_render.py` |
| Pantallas | `monitoreo.py` + `control_manual.py` | `pantalla_principal.py` (una sola) |

**Regla a seguir de ahora en adelante:** los nombres del **código** son canónicos; cuando se editen los
documentos de referencia, deben usar estos nombres.

### 4.2 Firmware: qué cubre cada pieza

- **Servidor TCP** (`comunicacion`): acepta 1 cliente a la vez, acumula bytes hasta `\n`, ignora `\r` y
  líneas vacías. Despachador con `aplicarComando()` reutilizable (soporta el comando `multi`).
- **Comandos entrantes:** `servo` (valida nombre + rango con `LIMITES[]`), `modo` (solo `automatico`/`manual`),
  `motor` (direcciones del d-pad), `multi` (lista de comandos en un mensaje).
- **Telemetría:** `enviarEstado()` ampliado: `bateria, modo, hay_advertencia, hay_error, distancia_cm,
  navegacion, consumo_watts, conexion_activa, cargando, tiempo_restante_min, posiciones_servos`.
  `distancia_cm` y `tiempo_restante_min` se mandan `null` cuando no hay lectura/estimación; `navegacion`
  es la maniobra decidida en automático.
- **Límites calibrados en firmware** (`comunicacion.cpp` `LIMITES[]`), iguales al mockup: cuello ±70°,
  hombros ±50°, pulgares ±22°. El sensor de distancia no está en `LIMITES[]` (es un sensor fijo y no recibe comandos de la
  app); los pulgares siguen por compatibilidad con la app, pero no tienen servo físico y se ignoran.
- **Navegación autónoma** (`auto`): máquina de estados de 3 ramas (avanzar / girar / alto), sin `delay()`
  y sin hardware propio — ver §3.2.1. El modo se sincroniza desde `comunicacion.modo()` con
  `modoAutonomo()`; al salir de automático los motores se detienen. La maniobra elegida viaja en el campo
  `navegacion` del estado, y en manual se reporta `"recto"` porque la maniobra es del operador.
- **Módulos (`config.h`):** flags de pruebas aisladas; módulo en 0 = no se inicializa y telemetría neutra.
  `lib/auto` no tiene flag propio: depende de `MODULOS.motores && MODULOS.distancia`.

---

## 5. Protocolo de comunicación (resumen vigente)

Medio: **WiFi TCP**, ESP32 como **servidor** (modo AP), JSON **una línea por mensaje** (`\n` delimita).

**ESP32 → PC:**
```json
{"tipo":"estado","bateria":0.83,"modo":"automatico","hay_advertencia":false,"hay_error":false,
 "distancia_cm":37.5,"navegacion":"recto","consumo_watts":4.2,"conexion_activa":true,"cargando":false,
 "tiempo_restante_min":null,
 "posiciones_servos":{"cuello":0,"hombro_izquierdo":10,"hombro_derecho":0,"pulgar_izquierdo":5,"pulgar_derecho":-5}}
{"tipo":"log","origen":"DISTANCIA","mensaje":"Obstáculo muy cerca: 8.0cm","nivel":"advertencia"}
```

**PC → ESP32:**
```json
{"tipo":"servo","servo":"cuello","angulo":30}
{"tipo":"modo","modo":"manual"}
{"tipo":"motor","direccion":"arriba"}
{"tipo":"multi","comandos":[{"tipo":"servo","servo":"cuello","angulo":10},{"tipo":"motor","direccion":"derecha"}]}
```

Reglas vigentes:
- `distancia_cm` y `tiempo_restante_min` **pueden venir como `null`** (sin lectura del sensor de
  distancia / sin estimación de batería). El parseo de `conexion.py` es **tolerante**: campos faltantes o `null` no pisan
  lo que `EstadoRobot` ya sabía (así conviven firmware viejo y nuevo).
- `navegacion` toma uno de `recto` | `izquierda` | `derecha` | `alto` (enum `Maniobra` en
  `app/nucleo/estado.py`). **Lo decide el ESP32** (`lib/auto`, ver §3.2.1); la app solo lo dibuja en
  la tarjeta NAVEGACIÓN. En modo manual siempre llega `"recto"`: la maniobra es del operador.
- `nivel_conexion` (`NivelConexion`) **no viaja en el JSON**: lo deriva la app por la frescura del último
  `estado` (ver §3.4). El robot solo manda el booleano `conexion_activa`.
- Envío de estado cada **~500 ms** (`config.h` `ENVIO_ESTADO_MS`). La GUI redibuja cada 60 ms.

Detalle, ejemplos de código y justificaciones (buffer de línea media, `setblocking(False)`, TCP como
flujo de bytes): ver [`protocolo_comunicacion_wifi_json.md`](protocolo_comunicacion_wifi_json.md).
(Nota: ese documento describe la base v1; los campos del estado ampliado están resumidos aquí y en las
cabeceras de `comunicacion.h`.)

---

## 6. Hoja de ruta y estado

Fases del plan, con su estado **al 15/10/2026**:

| Fase | Contenido | Estado |
|---|---|---|
| 1 · Estado | `EstadoRobot`, `Paleta`, `color_por_umbral`, Logger | ✅ **Hecho** (nucleo/) |
| 2 · Conexión | `Conexion` (ABC), `ComunicacionSimulada`, `Comunicacion` (TCP), `ConexionOffline` | ✅ **Hecho** |
| 3 · Interfaz gráfica | Widgets lógicos + renderers + pantalla única + `main.py` | ✅ **Hecho** (pruebas en `pruebas/`) |
| 4 · Lectura de sensores | Primer contacto con hardware real (ESP32 → PC) | 🔶 **Parcial**: sensor de distancia (HC-SR04) y batería (INA219) leídos en firmware; falta integrar y calibrar |
| 5 · Movimiento de servos/motores | GUI → ESP32 real, servos físicos | 🔶 **Parcial**: servos (ESP32Servo) y motores (TB6612FNG) implementados; **pendiente verificar cableado y dirección A/B de ruedas** |
| 6 · Modo automático | Máquina de estados de evasión en ESP32 | 🔶 **Parcial**: `lib/auto` implementa avanzar/girar/alto y ya alimenta el campo `navegacion`; **falta probar en hardware** (hoy `MODULOS.distancia = false`) y afinar la evasión (ver §7) |

**En paralelo (hardware/mecánico):** diseño 3D → cableado → integración → pulido. El software no se
bloquea por el hardware: la interfaz se termina aparte con `ComunicacionSimulada`.

---

## 7. Lo pendiente (priorizado)

### 7.1 Implementación (en orden sugerido)

1. **Probar la navegación autónoma en hardware** (`lib/auto`): poner `MODULOS.distancia` en `true` y
   verificar en el banco que avanza, gira a la derecha ante obstáculo y se detiene sin eco. Afinar la
   estrategia de evasión: hoy el giro es fijo a la derecha y no hay temporizador de giro (gira mientras
   siga detectando obstáculo).
2. **Completar la histéresis auto↔manual** (`TIEMPO_MANUAL_TIMEOUT_MS`): hoy el timeout, en manual, solo
   detiene los motores; falta que el robot **vuelva solo a automático** tras ese tiempo sin órdenes.
3. **Confirmar cableado real y direcciones de motores**: los pines de `pines.h` son propuesta de
   arranque; verificarlos contra [`esquema_de_conexion.md`](esquema_de_conexion.md), confirmar qué rueda es
   A/B en el TB6612FNG y que "arriba" avance hacia adelante.
4. **Calibración fina**: umbrales de batería (`BATERIA_VOLTAJE_MIN/MAX`, `CAPACIDAD_MAH`) contra el
   pack real; límites `LIMITES[]` contra las piezas impresas; `UMBRAL_OBSTACULO_CM` según el entorno.
5. **Activar el OLED** (flag `oled` → 1 en `config.h`) cuando la pantalla 0.96" esté cableada.
6. **Pulir los assets de `app/recursos/`**: exportar los SVG a PNG (fondo transparente) y ajustar tamaño
   de los ojos (`ALTO_OJO_IMAGEN` en `ojos_render.py`) y del recorte. `recoloreo.py` sigue vacío: hoy el
   tinte de los PNG lo hace `carga_recursos.py`; decidir si `recoloreo.py` se llena o se elimina.
7. **Alinear los documentos de referencia** (`protocolo_comunicacion_wifi_json.md`, `estructura_archivos…`)
   con los nombres y el protocolo vigentes (§4.1 y §5).

### 7.2 Decisiones pendientes

1. **Actualización de `EstadoRobot`**: hoy la GUI hace **polling** en el hilo principal
   (`recv()` no bloqueante cada 60 ms); si en la práctica congestiona, migrar a threading.
2. **Servos de los "ojos"**: el hardware los marca opcional/recomendado; en `PosicionServos` están
   comentados con "Aún no se ha decidido".
3. **Seguridad del movimiento** (parcial): `lib/auto` ya elige **girar** ante obstáculo y **frenar** sin
   eco; falta decidir con la mecánica si conviene frenar del todo (ambos `IN` en LOW) o mantener el giro,
   y si el "alto" por falta de eco debe ser permanente o reintentar tras un tiempo.

### 7.3 Calibraciones (valores de arranque, no definitivos)

| Parámetro | Valor inicial | Dónde | Estado |
|---|---|---|---|
| Timeout para salir de modo manual (histéresis) | 2000 ms | `config.h` (`TIEMPO_MANUAL_TIMEOUT_MS`) | usado para detener motores en manual; **falta el retorno automático** a automático |
| Umbral "obstáculo cercano" | 15 cm | `config.h` (`UMBRAL_OBSTACULO_CM`) | implementado (advertencia + evasión) |
| Estrategia de evasión | giro fijo a la derecha, sin temporizador | `auto.cpp` | provisional; afinar en hardware |
| Velocidad del d-pad / autónomo | 178/255 (~70 %) | `motores.cpp` (`VELOCIDAD_GIRO`) | provisional (motores 6 V, pack hasta 8.4 V) |
| Límites físicos de servos | cuello ±70°, hombros ±50°, pulgares ±22° | `comunicacion.cpp` `LIMITES[]` | verificar contra piezas reales |
| Buffer JSON firmware | `1024` estado/log · `4096` entrada | `comunicacion.cpp` | ok, crecer si el protocolo agrega campos |
| Periodo de telemetría | 500 ms (`ENVIO_ESTADO_MS`) · distancia 250 ms · batería 1000 ms | `config.h` | implementado |
| Estimación de batería | 6.6–8.4 V · 2000 mAh | `config.h` | recalibrar con el pack real |
| Pines y canales | propuesta de arranque | `pines.h` | **CONFIRMAR con el cableado** |
| Sentido de ruedas A/B | sin verificar | `motores.cpp` | confirmar en el robot |

### 7.4 Inconsistencias concretas (historial)

1. ✅ **RESUELTO (13/09/2026)** — `Comunicacion.actualizar_estado` guardaba `modo` como **string crudo**;
   ahora usa `Modo(...)`, consistente con el contrato del enum.
2. ✅ **RESUELTO (13/09/2026)** — El mensaje `estado` no traía `cargando`, `tiempo_restante_min`,
   `hay_advertencia`, `hay_error` ni `posiciones_servos`. Se amplió el protocolo en el firmware y el
   parseo de `conexion.py` es tolerante (campos `null`/ausentes no pisan valores, `distancia_cm` acepta `None`).
3. ✅ **RESUELTO (13/09/2026)** — `{"tipo":"multi",...}` estaba definido pero sin dispatcher encendido;
   ahora `procesarMensaje()` lo aplica vía `aplicarComando()`.
4. ✅ **RESUELTO (13/09/2026)** — `src/main.cpp` era la plantilla de PlatformIO (`myFunction`); ahora
   integra `lib/comunicacion`, crea el AP, inicializa módulos por flag y corre el loop no bloqueante.
5. **Vigente** — Los documentos de referencia (`protocolo_comunicacion_wifi_json.md`, `estructura_archivos…`)
   siguen con nombres/estructura antiguos (§4.1). El mockup `walle_demo.html` ya **no está** en el repo.
   Este documento, `esquema_de_conexion.md` y `pruebas/` son el punto de referencia.
6. **Vigente** — `recoloreo.py` está vacío, pero la GUI **ya usa Pillow** para teñir los PNG de
   `app/recursos/` (`carga_recursos.py`, §3.4); definir si `recoloreo.py` se llena con ese helper o se elimina.
7. ✅ **RESUELTO (15/10/2026)** — Se eliminó el concepto "radar": `lib/radar` → `lib/distancia`,
   `Radar` → `SensorDistancia`, pines `PIN_RADAR_*` → `PIN_US_*`, y la tarjeta GUI RADAR → **NAVEGACIÓN**
   (medidor de proximidad + maniobra). El HC-SR04 quedó como sensor fijo al frente.
8. ✅ **RESUELTO (15/10/2026)** — `lib/auto` reescrito e integrado en `main.cpp`. Antes no compilaba
   (faltaban includes, constructor con sintaxis inválida, `_sensor`/`_motores` sin constructor usable) y
   **duplicaba** los singletons `sensorDistancia`/`motores` sobre los mismos GPIO. Ahora usa los globales.
9. ✅ **RESUELTO (15/10/2026)** — `platformio.ini` movido a la raíz: se añadió `[platformio]` con
   `src_dir/lib_dir/include_dir = firmware/…` e `-Ifirmware/include`, porque el build fallaba con
   *"Nothing to build"*.
10. ✅ **RESUELTO (15/10/2026)** — La carpeta `pruebas/` volvió a la raíz (estaba bajo `firmware/pruebas/`,
    lo que rompía `raiz = Path(__file__).resolve().parent.parent` en `ejecutar_cajones.py`).
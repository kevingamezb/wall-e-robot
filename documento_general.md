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

**Hardware:** ESP32 (WiFi integrado), driver PCA9685 para servos (dir. 0x41), fuente separada para servos,
INA219 para consumo real (dir. 0x40), OLED I2C 0.96" (aún off), HC-SR04 (radar), L298N con 2 motores CC.
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
| Transición auto/manual | **Histéresis asimétrica**: fácil entrar a manual, difícil salir (timeout 2000 ms, a calibrar) |
| Comunicación | WiFi/TCP, **JSON una por línea** (`\n`), ESP32 como **servidor en modo AP** (`WALL-E`, IP 192.168.4.1, puerto 8080) |
| Pruebas de hardware aisladas | Flags 0/1 `MODULOS` en `firmware/include/config.h`; módulo en 0 reporta **valores neutros** a la GUI |
| Apagado | Corte físico de alimentación (relé/MOSFET), no sleep de software |

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
- `lib/servos` — PCA9685 (0x41), nombre→canal, canal 5 = radar.
- `lib/motores` — L298N diferencial (arriba/abajo/izquierda/derecha).
- `lib/radar` — HC-SR04 no bloqueante (máquina de estados por `micros()`) + barrido del servo-radar.
- `lib/bateria` — INA219 (0x40): nivel, corriente, watts, estimación de minutos.
- `lib/oled` — SSD1306 (código listo, flag `oled=0` en la 1ª entrega).

Cada módulo se activa con su flag en `include/config.h`. Con el flag en **0**, el módulo no se toca y la
telemetría manda valores neutros (baterías 1.0, consumo 0.0, distancia `null`) para que la GUI no grite
alertas falsas por hardware ausente. Cómo operar estas pruebas: ver [`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md).

### 3.3 Flujo de una vuelta de comunicación

1. ESP32 lee sensores → arma JSON `{"tipo":"estado", ...}` y lo envía cada **500 ms** (patrón `millis()`).
2. PC acumula bytes y, al aparecer `\n`, deserializa el JSON completo (buffer de línea media).
3. `tipo:"estado"` → escribe en `EstadoRobot` (parseo **tolerante**, campos faltantes/`null` no pisan valores);
   `tipo:"log"` → `estado.logger.agregar_linea(...)`.
4. Los widgets leen `EstadoRobot` y se redibujan.
5. El usuario mueve un control → PC arma `{"tipo":"servo"|"motor"|"modo"|"multi", ...}` y lo envía.
6. ESP32 valida servo + rango (`LIMITES[]`), modo o dirección y lo aplica sobre sus librerías de hardware.

---

## 4. Estado REAL del repositorio (actualizado)

```
wall-e-robot/
├── app/                                  # App de escritorio (Python). Paquete con __init__.py
│   ├── nucleo/
│   │   ├── estado.py        ✅ hecho     # Modo, NivelLog, EntradaLog, Logger, PosicionServos, EstadoRobot
│   │   └── paleta.py        ✅ hecho     # Paleta, PROPORCION_AUREA, color_por_umbral()
│   ├── comunicacion/
│   │   └── conexion.py      ✅ hecho     # Conexion (ABC), Comunicacion (TCP/real), ComunicacionSimulada,
│   │                                      # ConexionOffline, _procesar_mensaje() tolerante (protocolo ampliado)
│   ├── widgets/
│   │   ├── logica/          ✅ 9/9       # boton, deslizador, sol_bateria, barras_consumo, ojos,
│   │   │                                 # icono_sistema, radar, logger_widget, gamepad — TODOS con cajón de pruebas
│   │   └── renderizado/     ✅ 11/12     # *_render.py + base_render.py + tarjeta.py (recoloreo.py ⬜ vacío)
│   ├── pantallas/
│   │   ├── pantalla_principal.py ✅      # la única pantalla del sistema (monitoreo/control_manual eliminados)
│   │   └── iconos/          ⬜ vacío      # sin PNG: los íconos se dibujan por código
│   ├── main.py              ✅ hecho      # arranca la GUI: SIMULADOR → CONECTAR(IP) → DESCONECTAR
│   └── (sin requirements.txt — solo stdlib: tkinter, socket, json, random, time)
├── firmware/                            # ESP32 (PlatformIO) — COMPILA (Flash ~60%, RAM ~14%)
│   ├── include/
│   │   ├── pines.h          ✅ hecho     # GPIO, I2C (PCA9685 0x41, INA219 0x40), canales servo 0-4 + radar 5
│   │   └── config.h         ✅ hecho     # MODULOS (flags 0/1 de pruebas aisladas), AP WALL-E, umbrales y periodos
│   ├── src/main.cpp         ✅ hecho     # loop no bloqueante millis(); AP; init de módulos por flag; telemetría 500ms
│   ├── lib/
│   │   ├── comunicacion/    ✅ hecho     # servidor TCP; servo/modo/motor/multi; enviarEstado() ampliado; modo()
│   │   ├── servos/          ✅ hecho     # PCA9685, nombre→canal, moverRadar() (canal 5), angulosUsuario()
│   │   ├── motores/         ✅ hecho     # L298N diferencial (arriba/abajo/izquierda/derecha)
│   │   ├── radar/           ✅ hecho     # HC-SR04 no bloqueante + BarridoRadar (-45..45°)
│   │   ├── bateria/         ✅ hecho     # INA219: nivel, corriente, watts, minutos restantes
│   │   └── oled/            ✅ hecho     # SSD1306 (flag oled=0 por ahora; código listo)
│   └── platformio.ini       ✅ hecho     # libs Adafruit (Servo Driver, INA219, SSD1306/GFX) + ArduinoJson + -Iinclude
├── pruebas/
│   └── guia_de_pruebas.md   ✅ hecho     # cómo operar cajones, GUI simulado y pruebas aisladas de hardware
├── walle_demo.html                     # MOCKUP visual (NO es la app real; no refleja la pantalla única)
└── *.md                                # documentación (incluido este documento)
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
| Posición de ángulo | `distancia_obstaculo_cm` → `PosicionServos` | incluye `radar_us`; ojos comentados |
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
  consumo_watts, conexion_activa, cargando, tiempo_restante_min, posiciones_servos`.
  `distancia_cm` y `tiempo_restante_min` se mandan `null` cuando no hay lectura/estimación.
- **Límites calibrados en firmware** (`comunicacion.cpp` `LIMITES[]`), iguales al mockup: cuello ±70°,
  hombros ±50°, pulgares ±22°. El canal 5 (radar) queda fuera de `LIMITES[]` y gira autónomo.
- **Módulos (`config.h`):** flags de pruebas aisladas; módulo en 0 = no se inicializa y telemetría neutra.

---

## 5. Protocolo de comunicación (resumen vigente)

Medio: **WiFi TCP**, ESP32 como **servidor** (modo AP), JSON **una línea por mensaje** (`\n` delimita).

**ESP32 → PC:**
```json
{"tipo":"estado","bateria":0.83,"modo":"automatico","hay_advertencia":false,"hay_error":false,
 "distancia_cm":37.5,"consumo_watts":4.2,"conexion_activa":true,"cargando":false,
 "tiempo_restante_min":null,
 "posiciones_servos":{"cuello":0,"hombro_izquierdo":10,"hombro_derecho":0,"pulgar_izquierdo":5,"pulgar_derecho":-5}}
{"tipo":"log","origen":"RADAR","mensaje":"Obstáculo muy cerca: 8.0cm","nivel":"advertencia"}
```

**PC → ESP32:**
```json
{"tipo":"servo","servo":"cuello","angulo":30}
{"tipo":"modo","modo":"manual"}
{"tipo":"motor","direccion":"arriba"}
{"tipo":"multi","comandos":[{"tipo":"servo","servo":"cuello","angulo":10},{"tipo":"motor","direccion":"derecha"}]}
```

Reglas vigentes:
- `distancia_cm` y `tiempo_restante_min` **pueden venir como `null`** (sin lectura de radar / sin
  estimación de batería). El parseo de `conexion.py` es **tolerante**: campos faltantes o `null` no pisan
  lo que `EstadoRobot` ya sabía (así conviven firmware viejo y nuevo).
- Envío de estado cada **~500 ms** (`config.h` `ENVIO_ESTADO_MS`). La GUI redibuja cada 60 ms.

Detalle, ejemplos de código y justificaciones (buffer de línea media, `setblocking(False)`, TCP como
flujo de bytes): ver [`protocolo_comunicacion_wifi_json.md`](protocolo_comunicacion_wifi_json.md).
(Nota: ese documento describe la base v1; los campos del estado ampliado están resumidos aquí y en las
cabeceras de `communicacion.h`.)

---

## 6. Hoja de ruta y estado

Fases del plan, con su estado **al 13/09/2026**:

| Fase | Contenido | Estado |
|---|---|---|
| 1 · Estado | `EstadoRobot`, `Paleta`, `color_por_umbral`, Logger | ✅ **Hecho** (nucleo/) |
| 2 · Conexión | `Conexion` (ABC), `ComunicacionSimulada`, `Comunicacion` (TCP), `ConexionOffline` | ✅ **Hecho** |
| 3 · Interfaz gráfica | Widgets lógicos + renderers + pantalla única + `main.py` | ✅ **Hecho** (pruebas en `pruebas/`) |
| 4 · Lectura de sensores | Primer contacto con hardware real (ESP32 → PC) | 🔶 **Parcial**: radar (HC-SR04) y batería (INA219) leídos en firmware; falta integrar y calibrar |
| 5 · Movimiento de servos/motores | GUI → ESP32 real, servos físicos | 🔶 **Parcial**: servos (PCA9685) y motores (L298N) implementados; **pendiente verificar cableado y dirección A/B de ruedas** |
| 6 · Modo automático | Máquina de estados de evasión en ESP32 | ⬜ Pendiente |

**En paralelo (hardware/mecánico):** diseño 3D → cableado → integración → pulido. El software no se
bloquea por el hardware: la interfaz se termina aparte con `ComunicacionSimulada`.

---

## 7. Lo pendiente (priorizado)

### 7.1 Implementación (en orden sugerido)

1. **Modo automático en el firmware** (`src/main.cpp`): evasión por estados, aplicar la histéresis
   auto↔manual (`TIEMPO_MANUAL_TIMEOUT_MS`) y detener/evitar los motores ante obstáculo cercano.
2. **Confirmar cableado real y direcciones de motores**: los pines de `pines.h` son propuesta de
   arranque; verificar qué rueda es A/B en el L298N y que "arriba" avance hacia adelante.
3. **Calibración fina**: umbrales de batería (`BATERIA_VOLTAJE_MIN/MAX`, `CAPACIDAD_MAH`) contra el
   pack real; límites `LIMITES[]` contra las piezas impresas; `UMBRAL_OBSTACULO_CM` según el entorno.
4. **Activar el OLED** (flag `oled` → 1 en `config.h`) cuando la pantalla 0.96" esté cableada.
5. **Llenar `app/widgets/renderizado/recoloreo.py`** o documentar su supresión: hoy la GUI dibuja
   íconos por código Tkinter y no usa Pillow/PNG (decisión v3).
6. **Alinear los documentos de referencia** (`protocolo_comunicacion_wifi_json.md`, `estructura_archivos…`)
   con los nombres y el protocolo vigentes (§4.1 y §5). `walle_demo.html` tampoco refleja la pantalla única.

### 7.2 Decisiones pendientes

1. **Actualización de `EstadoRobot`**: hoy la GUI hace **polling** en el hilo principal
   (`recv()` no bloqueante cada 60 ms); si en la práctica congestiona, migrar a threading.
2. **Servos de los "ojos"**: el hardware los marca opcional/recomendado; en `PosicionServos` están
   comentados con "Aún no se ha decidido".
3. **Seguridad del movimiento**: en modo automático, política exacta para detener motores ante
   obstáculo (freno del L298N vs. giro) — a definir con la mecánica.

### 7.3 Calibraciones (valores de arranque, no definitivos)

| Parámetro | Valor inicial | Dónde | Estado |
|---|---|---|---|
| Timeout para salir de modo manual (histéresis) | 2000 ms | `config.h` (`TIEMPO_MANUAL_TIMEOUT_MS`) | pendiente de usar (modo automático) |
| Umbral "obstáculo cercano" | 15 cm | `config.h` (`UMBRAL_OBSTACULO_CM`) | implementado (advertencia) |
| Límites físicos de servos | cuello ±70°, hombros ±50°, pulgares ±22° | `comunicacion.cpp` `LIMITES[]` | verificar contra piezas reales |
| Buffer JSON firmware | `1024` estado/log · `4096` entrada | `comunicacion.cpp` | ok, crecer si el protocolo agrega campos |
| Periodo de telemetría | 500 ms (`ENVIO_ESTADO_MS`) · radar 250 ms · batería 1000 ms | `config.h` | implementado |
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
5. **Vigente** — Los documentos de referencia siguen con nombres/estructura antiguos (§4.1), y
   `walle_demo.html` no refleja la pantalla única. Este documento y `pruebas/` son el punto de referencia.
6. **Vigente** — `recoloreo.py` está vacío y la GUI no usa Pillow (íconos por código); definir si se
   llena con el helper o se elimina.
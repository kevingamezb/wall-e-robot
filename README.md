# Wall-E Robot

Robot Wall-E con ESP32: se mueve de forma autónoma evadiendo obstáculos, se controla
manualmente desde una app de escritorio por WiFi y muestra su estado (batería, sensores,
modo) con una estética inspirada en la película.

Este README es el punto de entrada al repositorio. El detalle de cada tema vive en los
documentos especializados enlazados más abajo.

---

## Descripción

- **App de escritorio (PC):** Python + Tkinter. Se conecta al robot por WiFi/TCP, dibuja el
  panel de control y compone los comandos. Puede funcionar sin hardware usando un simulador.
- **Firmware (ESP32):** C++ / PlatformIO. Lee sensores, mueve servos y motores, decide la
  navegación autónoma y expone un servidor TCP con mensajes JSON de una línea.
- **Comunicación:** WiFi/TCP con el ESP32 en modo AP (red `WALL-E`, `192.168.4.1`, puerto
  `8080`). El robot envía telemetría cada ~500 ms y recibe comandos de la app.

## Hardware

- ESP32 (WiFi integrado).
- 3 servos MG90S (cuello + 2 brazos) alimentados por un buck de 5 V.
- Driver TB6612FNG con 2 motores CC.
- INA219 para consumo real (I2C `0x40`).
- OLED SSD1306 0.96" (I2C `0x3C`).
- HC-SR04 como sensor de distancia fijo al frente.
- 2 LEDs indicadores (rojo/amarillo).

El cableado completo, la alimentación y la tierra común están en
[`esquema_de_conexion.md`](esquema_de_conexion.md), que a su vez remite a los pines
canónicos en [`firmware/include/pines.h`](firmware/include/pines.h).

## Arquitectura

### App de escritorio (PC)

Cuatro capas; cada capa solo conoce la de abajo:

1. **Comunicación** — `app/comunicacion/conexion.py` (`Conexion`, `Comunicacion` TCP,
   `ComunicacionSimulada`, `ConexionOffline`).
2. **Modelo de datos** — `app/nucleo/` (`EstadoRobot`, `Paleta`).
3. **Widgets** — `app/widgets/logica/` (sin Tkinter) + `app/widgets/renderizado/` (con Tkinter).
4. **Pantallas** — `app/pantallas/` (`pantalla_principal.py`, `modal_controles.py`).

`EstadoRobot` es una caja de datos compartida: quien produce información escribe ahí y quien
la consume lee de ahí, sin conocerse entre sí. Los controles interactivos usan callbacks.

### Firmware (ESP32)

Una librería por componente bajo `firmware/lib/`, orquestada por `firmware/src/main.cpp` con
un loop no bloqueante (`millis()`, sin `delay()`): `comunicacion`, `servos`, `motores`,
`distancia`, `bateria`, `oled`, `leds`, `auto`, `ota`.

`lib/auto` no tiene hardware propio: decide usando los módulos globales de distancia y
motores (`iniciar()`, `actualizar()`, `modoAutonomo()`, `hayObstaculo()`, `navegacion()`).

Cada módulo de hardware se activa con un flag en
[`firmware/include/config.h`](firmware/include/config.h). Un módulo desactivado no se toca y
reporta valores neutros a la GUI, para no generar alertas falsas por hardware ausente.

## Comunicación (resumen)

Medio WiFi/TCP, JSON de una línea por mensaje (`\n` como delimitador). El ESP32 actúa como
servidor en modo AP.

- **ESP32 → PC:** `{"tipo":"estado", ...}` (telemetría) y `{"tipo":"log", ...}`.
- **PC → ESP32:** `{"tipo":"servo"|"modo"|"motor"|"multi", ...}`.

La app aplica un parseo tolerante: campos ausentes o `null` no pisan el valor anterior, de
modo que firmware viejo y nuevo conviven. El nivel de conexión no viaja en el JSON: la app lo
deriva por la frescura del último estado recibido.

Los pines y el cableado están en [`esquema_de_conexion.md`](esquema_de_conexion.md); el
protocolo y la operación detallada, en
[`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md).

## Estructura del repositorio

```text
wall-e-robot/
├── app/                    # App de escritorio (Python + Tkinter). Depende de Pillow.
│   ├── nucleo/             # EstadoRobot, Paleta
│   ├── comunicacion/       # TCP/JSON + simulador + offline
│   ├── widgets/logica/     # Lógica de widgets (sin Tkinter)
│   ├── widgets/renderizado/# Renderers y helpers de dibujo (con Tkinter)
│   ├── pantallas/          # pantalla_principal, modal_controles
│   ├── recursos/           # Assets PNG (ojos e íconos), teñidos con la Paleta
│   └── main.py             # Arranque de la GUI
├── firmware/               # Firmware del ESP32 (PlatformIO)
│   ├── include/            # pines.h, config.h, secrets.example.h
│   ├── lib/                # Una librería por componente (+ ota)
│   └── src/main.cpp        # Loop no bloqueante
├── configuracion/          # controles.json (mapeo de teclas persistente)
├── pruebas/                # Runner de cajones + guia_de_pruebas.md
├── tests/                  # Suite automatizada con pytest
├── scripts/                # Utilidades de build (manifiesto OTA)
├── esquema_de_conexion.md  # Cableado por componente
├── platformio.ini          # Configuración del build del firmware
├── requirements.txt        # Dependencias de la app (Pillow)
└── requirements-dev.txt    # Dependencias de desarrollo (pytest, pytest-cov)
```

## Cómo empezar

### Requisitos

- Python 3.10 o superior con Tkinter.
- Dependencias de la app: `python -m pip install -r requirements.txt`.
- Dependencias de desarrollo (pruebas): `python -m pip install -r requirements-dev.txt`.
- Firmware: PlatformIO (extensión de VS Code o CLI).

### Ejecutar la app (simulador)

Desde la **raíz** del repositorio:

```powershell
python -m app.main
```

Arranca con el simulador conectado (no requiere ESP32).

### Ejecutar las pruebas

```powershell
python -m pytest                 # suite automatizada (tests/)
python pruebas/ejecutar_cajones.py   # cajones manuales heredados
```

Detalles, cobertura y notas de VS Code: [`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md).

### Compilar y flashear el firmware

```powershell
pio run              # compilar
pio run -t upload    # compilar + grabar por USB
pio device monitor   # monitor serial (115200)
```

Si `pio` no está en el PATH, usa la ruta del entorno:
`C:\Users\<usuario>\.platformio\penv\Scripts\platformio.exe`.

### Actualización OTA (por WiFi)

El firmware incorpora un portal web OTA y `ArduinoOTA` (ver la carpeta `firmware/lib/ota/`),
con verificación por MD5 y una guardia de rollback. Las credenciales se toman de
`firmware/include/secrets.h` (plantilla en
[`firmware/include/secrets.example.h`](firmware/include/secrets.example.h)); ese archivo no se
versiona.

El procedimiento, el manifiesto MD5 y las comprobaciones de rollback están documentados en
[`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md) (§7). **La actualización OTA está
implementada y documentada, pero no se declara validada en hardware en este README.**

## Estado del proyecto

- App de escritorio: interfaz completa y usable con simulador.
- Firmware: comunica, lee sensores y mueve servos/motores; integrándose con hardware real.
- Pruebas: suite automatizada (pytest) más los cajones manuales heredados.
- Pendiente: validar cableado y direcciones de motores, calibrar umbrales, afinar la
  navegación autónoma en hardware y validar OTA en el robot.

## Documentación

- [`esquema_de_conexion.md`](esquema_de_conexion.md) — cableado por componente.
- [`pruebas/guia_de_pruebas.md`](pruebas/guia_de_pruebas.md) — operación, pruebas y OTA.

## Licencia

Ver [`LICENSE`](LICENSE).

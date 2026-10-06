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
├── app/            # App de escritorio (Python + Tkinter). Solo librería estándar.
├── firmware/       # Firmware del ESP32 (PlatformIO / C++). Librerías usadas se
│                   # descargan solas al compilar (ingresar a la red).
└── documento_general.md   # Referencia del estado y decisiones del proyecto.
```

Todas las pruebas del lado **PC** se ejecutan desde la raíz del repositorio
(la carpeta donde está `app/`), NO dentro de `app/`.

---

## 2. Requisitos

| Componente | Requisito | Notas |
|---|---|---|
| PC | Python 3.10 o superior con Tkinter | No hace falta `pip install` nada: la app usa solo la librería estándar. |
| ADVERTENCIA DEL FIRMWARE | PlatformIO | En VS Code: instalar la extensión "PlatformIO IDE". O usar la CLI (ver §4). |

> Los íconos y colores de la GUI se dibujan por código (Tkinter), no se usan imágenes externas.

---

## 3. Pruebas del lado PC (sin hardware) — "Cajones de prueba"

Cada módulo trae su propio cajón de pruebas (bloque `if __name__ == "__main__"`): al ejecutarlo
imprime `Pruebas OK` si todo está bien. Se ejecutan desde la **raíz del repositorio**:

```powershell
python -m app.nucleo.estado
python -m app.nucleo.paleta
python -m app.comunicacion.conexion
python -m app.widgets.logica.boton
python -m app.widgets.logica.deslizador
python -m app.widgets.logica.gamepad
python -m app.widgets.logica.ojos
python -m app.widgets.logica.icono_sistema
python -m app.widgets.logica.sol_bateria
python -m app.widgets.logica.barras_consumo
python -m app.widgets.logica.radar
python -m app.widgets.logica.logger_widget
```

Qué revisa cada uno (resumen):

| Cajón | Prueba |
|---|---|
| `nucleo.estado` | `EstadoRobot`, `Modo`, `NivelLog`, `Logger` |
| `nucleo.paleta` | Colores centralizados y `color_por_umbral()` |
| `comunicacion.conexion` | Simulador, `ConexionOffline` y **el parseo tolerante del protocolo real** (campos nuevos, `null`, `posiciones_servos`) |
| `widgets.logica.gamepad` | Direcciones del d-pad (`{"tipo":"motor",...}`), servos del cuello y pulgares, reposo, y que **sin conexión no envía nada** |
| `widgets.logica.boton` / `deslizador` | Suscripción/avisos, hover, estados de color |
| demás `widgets.*` | Lógica de cada widget de la pantalla |

### 3.1 La GUI completa en modo simulado

```powershell
python -m app.main
```

- Arranca con **`SIMULADOR`** conectado (no requiere ESP32).
- Debe mostrarse la pantalla única con: Estado (columna central con 5 barras), Radar, Ojos,
  Sol de batería, Consumo, Logger, Gamepad y botones **CONECTAR / DESCONECTAR**.
- El simulador genera datos que cambian solos (batería baja lentamente, distancia varía,
  log de prueba cada 10 s) y alertas (obstáculo cerca < 15 cm, batería baja < 0.25).
- Para cerrar: `Ctrl+C` en la terminal o cerrar la ventana.

> Si algo sale mal aquí, el problema es de la app; el hardware no tiene nada que ver.

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
MODULO radar     = activo
MODULO bateria   = INACTIVO (flag=0)
MODULO motores   = INACTIVO (flag=0)
MODULO oled      = INACTIVO (flag=0)
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
    bool servos;   // PCA9685 + servos de usuario (canales 0-4)
    bool radar;    // HC-SR04 + servo de barrido (canal 5)
    bool bateria;  // INA219 (voltaje/corriente)
    bool oled;     // SSD1306 0.96" (se dejó apagado en la 1ª entrega)
    bool motores;  // L298N, 2 motores CC (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, true, false, false, false };
```

**Configuración de fábrica (1ª entrega):** `servos` y `radar` activos; `bateria`, `oled` y
`motores` en 0.

**Reglas de comportamiento:**

- Un módulo en **0** no se inicializa, no se mueve ni se lee, y **la GUI ve valores neutros**
  (batería 1.0, consumo 0.0, distancia sin lectura). Así el panel no grita alertas falsas
  por hardware que no está conectado.
- Los servos tienen su propio listado `SERVOS_ACTIVOS[]` (mismo orden que los canales 0-4):
  `cuello, hombro_izquierdo, hombro_derecho, pulgar_izquierdo, pulgar_derecho`.
  Incluso con un servo en 0, la telemetría manda el ángulo que la GUI cree que se pidió.
- El **servo del radar (canal 5)** es autónomo: lo mueve el firmware en el barrido −45 a +45
  grados. NO se le puede ordenar desde la app, y no va en `SERVOS_ACTIVOS[]`.

### 5.1 Procedimiento genérico de prueba de un módulo

1. Conectar el ESP32 por USB al PC y tener el monitor serial abierto.
2. En `config.h`, poner en **1** solo el módulo que se va a probar (y en 0 los demás).
3. Compilar + grabar (`pio run -t upload`).
4. Conectar el PC a la red WiFi **WALL-E** (clave `wall-e-robot`).
5. Lanzar la app: `python -m app.main` → **CONECTAR** → IP `192.168.4.1` (puerto por defecto).
6. Operar el control y comprobar: el componente responde y el monitor serial muestra los comandos.

### 5.2 Pruebas orientativas por módulo

| Módulo | Cómo probarlo | Qué se espera |
|---|---|---|
| **Servos** (flag `servos=1`) | Mover el deslizador del **cuello** y los **pulgares** en la GUI; presionar **REPOSO**. | Los servos se mueven suaves. Serial: `Servo 'cuello' -> 30 grados.` |
| **Motores** (flag `motores=1`) | Mantener el d-pad en direcciones: **arriba / abajo / izquierda / derecha**. | Las 2 ruedas giran: adelante, atrás, y giro en el sitio. Serial: `Motor -> arriba`. |
| **Radar** (flags `servos=1, radar=1`) | Poner la mano frente al sensor a < 15 cm. | El servo del radar barre solo; al acercar la mano aparece la **advertencia** en la GUI y el log `Obstáculo muy cerca: X.Xcm`. |
| **Batería** (flag `bateria=1`) | Mirar el Sol de batería y el consumo con el robot alimentado y en reposo/operando. | El nivel se calcula del voltaje medido por el INA219 y baja conforme se descarga la batería. Log crítico (rojo) si el nivel cae por debajo de 0.10. |
| **OLED** (flag `oled=1`) | Ninguna acción extra. | La pantalla 0.96" muestra BAT / DIS / MODO / CONECTADO. |

> **IMPORTANTE — cables todavía sin confirmar:** los pines de `firmware/include/pines.h` y el
> sentido A/B de las ruedas del L298N son **propuesta de arranque**. Antes de la primera prueba
> de motores, verificar: qué rueda es A y cuál B (IN1/IN2 vs IN3/IN4) y que girar "arriba"
> mueve el robot hacia adelante. Si sale al revés, se canjea A↔B en `lib/motores/motores.cpp`.

### 5.3 Cableado resumido (según `pines.h`)

| Señal | Pin ESP32 |
|---|---|
| I2C SDA / SCL | 21 / 22 |
| HC-SR04 TRIG / ECHO | 5 / 18 |
| L298N IN1..IN4 / ENA / ENB | 13, 12, 14, 27 / 26 / 25 |

- PCA9685 en dirección **0x41** (puente A0 soldado; de fábrica viene en 0x40).
- INA219 en dirección **0x40** (sin puentes).
- Canales PCA9685: 0 cuello, 1 hombro_izquierdo, 2 hombro_derecho, 3 pulgar_izquierdo,
  4 pulgar_derecho, **5 radar**.
- Fuente externa para los servos; GND común con el ESP32.

---

## 6. Conectar la app al ESP32 real

1. Encender el ESP32 (debe aparecer la red **WALL-E**).
2. PC → conectarse a esa red WiFi (clave `wall-e-robot`).
3. Abrir la app (`python -m app.main`).
4. Presionar **CONECTAR**, confirmar IP `192.168.4.1` y CONECTAR.
   - Si la IP no funciona, leer la IP real que imprimió el Serial del ESP32.
5. Al conectar: el indicador pasa de **SIN CONEXIÓN** a **conectado** y se ve en el estado.
6. Para volver al simulador: **DESCONECTAR** deja el panel sin conexión (no vuelve al simulador).

---

## 7. El protocolo en 30 segundos (para depurar)

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
 "distancia_cm":12.3,"consumo_watts":3.4,"conexion_activa":true,"cargando":false,
 "tiempo_restante_min":42,"posiciones_servos":{"cuello":0,"hombro_izquierdo":10,"hombro_derecho":0,"pulgar_izquierdo":5,"pulgar_derecho":-5}}
{"tipo":"log","origen":"RADAR","mensaje":"Obstáculo muy cerca: 8.0cm","nivel":"advertencia"}
```

Detalles útiles:
- `distancia_cm` y `tiempo_restante_min` pueden venir como **null** (sin lectura de radar /
  sin estimación de batería). La app lo interpreta como "no tocar ese dato".
- Límites físicos validados en el firmware (`LIMITES[]` en `lib/comunicacion`):
  cuello ±70°, hombros ±50°, pulgares ±22°. Un ángulo fuera de rango se rechaza.
- El ESP32 envía un estado cada **~500 ms**; la GUI redibuja cada 60 ms.

---

## 8. Alertas (advertencia / error)

| Señal | Criterio actual (firmware) | Qué ves en la GUI |
|---|---|---|
| `hay_advertencia` | Radar activo y distancia ≤ **15 cm** | Ícono de advertencia + log naranja `RADAR` |
| `hay_error` | Batería activa y nivel < **0.10** | Ícono de error + log rojo `BATERIA` |

Los logs de alerta se emiten **solo al transicionar** (se posan mientras la alerta persiste), para
no llenar el Logger de repeticiones.

---

## 9. Solución de problemas (rápido)

| Síntoma | Causa probable / acción |
|---|---|
| `ModuleNotFoundError` al correr un cajón | Se ejecutó desde dentro de `app/`. Correr desde la **raíz** del repositorio. |
| `pio` no es un comando reconocido | Usar la ruta del entorno: `C:\Users\<usuario>\.platformio\penv\Scripts\platformio.exe` |
| Monitor serial no da la línea "AP iniciada..." | Bajar la velocidad del monitor a **115200**; revisar el puerto USB (Upload). |
| "No se pudo conectar" en la GUI | El PC no está en la red **WALL-E**, el ESP32 no arrancó, o la IP no es `192.168.4.1`. Revisar Serial. |
| La GUI no marca falso el hardware ausente | Un módulo en **0** reporta neutro; si algo alerta sin hardware, revisar que su flag esté en 0. |
| Un servo no se mueve | Verificar fuente externa de 5-6V para servos, GND común, y el puente A0 del PCA9685 (0x41). |
| Las ruedas giran al revés / invertidas | Cangejar A↔B en `lib/motores/motores.cpp` y confirmar ruedas en `pines.h`. |
| WARNING "Ignore unknown configuration option `monitor_filter`" | Inofensivo: el pio local no reconoce esa clave opcional. Ignorar. |

---

## 10. Checklist de prueba (marcar cada ítem completado)

**Lado PC (sin hardware):**
- [ ] Todos los cajones de §3 imprimen `Pruebas OK`.
- [ ] `python -m app.main` abre la pantalla única en modo SIMULADOR.
- [ ] El gamepad sin conexión no emite comandos (overlay SIN CONEXIÓN visible).

**Lado firmware aislado:**
- [ ] Firma con solo `servos=1`: deslizadores mueven cuello y pulgares; REPOSO los centra.
- [ ] Solo `motores=1`: d-pad mueve las ruedas en las 4 direcciones.
- [ ] `radar=1` (+ servos=1): el servo del radar barre solo y la mano cerca (< 15 cm) dispara advertencia.
- [ ] La GUI conectada a `192.168.4.1` muestra el estado real (no neutro) de los módulos activos.
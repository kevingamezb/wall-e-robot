# Esquema de conexión

Cableado físico del robot Wall-E. El ESP32 es el nodo central: cada componente termina
en uno de sus GPIO o en el riel de alimentación compartido.

**Formato de cada línea:** `PIN(Componente) - PIN(Componente)`
(izquierda = pin sobre el componente que da la sección; derecha = pin del otro extremo,
seguido del componente al que pertenece).

> **Contrato de pines.** Los pines lógicos canónicos están en
> [`firmware/include/pines.h`](firmware/include/pines.h): `PIN_US_*`, `PIN_MOTOR_*`,
> `PIN_SERVO_*`, `PIN_LED_*`, `PIN_I2C_*`. Si cambia un cable, se cambia ahí.

> **Tierra común.** Todo comparte un único `GND(Común)`: ESP32, batería, buck de 5 V,
> TB6612FNG, servos, LEDs, HC-SR04, INA219 y OLED. Sin esa tierra única no hay señal.

---

## ESP32

Alimentación lógica, bus I2C compartido y punto de referencia de GND.

- `VIN(ESP32) - 5V(Fuente)` (buck de 5 V; por USB también se alimenta)
- `GND(ESP32) - GND(Común)`
- `3.3V(ESP32) - VCC(INA219)` (regulador interno del ESP32, solo carga lógica)
- `3.3V(ESP32) - VCC(OLED)`
- `3.3V(ESP32) - VCC(TB6612FNG)` (lógica; con VCC = 3.3 V los GPIO alto = 3.3 V cumplen VIH)
- `GPIO21(ESP32) - SDA(INA219)` · `GPIO21(ESP32) - SDA(OLED)` (bus I2C compartido)
- `GPIO22(ESP32) - SCL(INA219)` · `GPIO22(ESP32) - SCL(OLED)`

---

## HC-SR04 (sensor de distancia ultrasónico, fijo al frente)

Sin servomotor: apuntado fijo hacia adelante.

- `VCC(HC-SR04) - 5V(Fuente)`
- `GND(HC-SR04) - GND(Común)`
- `TRIG(HC-SR04) - GPIO17(ESP32)`
- `ECHO(HC-SR04) - GPIO16(ESP32)` · **divisor 1 kΩ / 2 kΩ** antes del GPIO

> **⚠️ ECHO es de 5 V y el ESP32 es de 3.3 V.** Sin el divisor, el eco quema el GPIO 16.
> Circuito: `ECHO -[1kΩ]- nodo -[2kΩ]- GND`, y `GPIO16(ESP32) - nodo` (3.33 V exactos).

---

## TB6612FNG (driver de motores CC)

- `VCC(TB6612FNG) - 3.3V(ESP32)` (lógica) · `GND(TB6612FNG) - GND(Común)`
- `VM(TB6612FNG) - VOUT(Relé/MOSFET)` (alimentación de motores, ~7.4 V)
- `STBY(TB6612FNG) - GPIO4(ESP32)` (el firmware lo pone en alto; sin esto no mueve nada)
- `PWMA(TB6612FNG) - GPIO25(ESP32)`
- `AIN1(TB6612FNG) - GPIO26(ESP32)` · `AIN2(TB6612FNG) - GPIO27(ESP32)`
- `PWMB(TB6612FNG) - GPIO33(ESP32)`
- `BIN1(TB6612FNG) - GPIO32(ESP32)` · `BIN2(TB6612FNG) - GPIO14(ESP32)`
- `AO1(TB6612FNG) - +(Motor A)` · `AO2(TB6612FNG) - -(Motor A)`
- `BO1(TB6612FNG) - +(Motor B)` · `BO2(TB6612FNG) - -(Motor B)`

---

## Motor A (rueda izquierda)

- `+(Motor A) - AO1(TB6612FNG)` · `-(Motor A) - AO2(TB6612FNG)`

## Motor B (rueda derecha)

- `+(Motor B) - BO1(TB6612FNG)` · `-(Motor B) - BO2(TB6612FNG)`

> **⚠️ pendiente de verificar:** qué rueda es canal A / canal B y si "arriba" (PWM
> positivo en ambos) avanza hacia adelante. Si gira al revés, se cambia el cable
> (+/−) de esa rueda, no el código.

---

## Servo cuello MG90S

- `Señal(Servo cuello) - GPIO23(ESP32)`
- `VCC(Servo cuello) - 5V(Fuente)` · `GND(Servo cuello) - GND(Común)`

## Servo brazo izquierdo MG90S

- `Señal(Servo brazo izq) - GPIO18(ESP32)`
- `VCC(Servo brazo izq) - 5V(Fuente)` · `GND(Servo brazo izq) - GND(Común)`

## Servo brazo derecho MG90S

- `Señal(Servo brazo der) - GPIO19(ESP32)`
- `VCC(Servo brazo der) - 5V(Fuente)` · `GND(Servo brazo der) - GND(Común)`

> **⚠️ los MG90S nunca se alimentan del GPIO ni del 3.3 V del ESP32.** Van al buck de
> 5 V por su propio cable; el ESP32 solo aporta la señal de control.

> **⚠️ dos pines de `pines.h` (`PIN_SERVO_BRAZO_IZQ`, `PIN_SERVO_BRAZO_DER`) y un canal de
> `SERVOS_ACTIVOS[]`** se conservan en el protocolo aunque solo haya 3 servos físicos.

---

## INA219 (medida de consumo)

Dir. I2C `0x40` (sin puentes). Va **en serie** en el positivo para medir corriente.

- `VCC(INA219) - 3.3V(ESP32)` · `GND(INA219) - GND(Común)`
- `SDA(INA219) - GPIO21(ESP32)` · `SCL(INA219) - GPIO22(ESP32)`
- `+(Batería) - VIN+(INA219)` (alimentación que entra a la tarjeta)
- `VIN-(INA219) - VIN(Relé/MOSFET)` (lo que sale ya mide la corriente de todo el robot)

---

## OLED SSD1306 0.96"

Dir. I2C `0x3C` (sin puentes).

- `VCC(OLED) - 3.3V(ESP32)` · `GND(OLED) - GND(Común)`
- `SDA(OLED) - GPIO21(ESP32)` · `SCL(OLED) - GPIO22(ESP32)`

> **I2C compartido:** `SDA` y `SCL` son el mismo par de hilos para el INA219 y el OLED
> (por eso las dos líneas aparecen dos veces). Si en el banco queda todo conectado,
> agrega **pull-ups de 4.7 kΩ** a `3.3V(ESP32)`; si no, los lleva incorporados la
> mayoría de los módulos.

---

## LEDs indicadores

Con **resistencia de 220 Ω** en serie entre el GPIO y el ánodo (salvo el verde).

- `Ánodo(LED rojo) - GPIO13(ESP32)` · `Cátodo(LED rojo) - GND(Común)`
- `Ánodo(LED amarillo) - GPIO2(ESP32)` · `Cátodo(LED amarillo) - GND(Común)`
- `Ánodo(LED verde) - 5V(Fuente)` · `Cátodo(LED verde) - GND(Común)` · **sin GPIO** (encendido fijo)

---

## Alimentación

Batería LiPo 2S (8.4 V llena, 6.6 V mínima, 2000 mAh) → protección → buck → cargas.

- `+(Batería) - VIN+(INA219)` · `GND(Batería) - GND(Común)`
- `VIN-(INA219) - VIN(Relé/MOSFET)`
- `VOUT(Relé/MOSFET) - VM(TB6612FNG)` (motores)
- `VOUT(Relé/MOSFET) - IN+(Buck 5V)` (carga lógica y servos)
- `OUT+(Buck 5V) - VCC(HC-SR04)` · `OUT+(Buck 5V) - VCC(Servos cuello / brazo izq / brazo der)`
- `OUT+(Buck 5V) - Ánodo(LED verde)` · `OUT+(Buck 5V) - VIN(ESP32)`
- `OUT-(Buck 5V) - GND(Común)`
- `GND(Común) - GND(ESP32)` · `GND(Común) - GND(INA219)` · `GND(Común) - GND(OLED)`
  · `GND(Común) - GND(TB6612FNG)` · `GND(Común) - GND(HC-SR04)` · `GND(Común) - GND(Servos)`

> **⚠️ el corte de alimentación es físico** (relé/MOSFET). No hay GPIO en `pines.h`
> que lo controle: es un interruptor, no un sleep de software.

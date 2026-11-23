#ifndef PINES_H
#define PINES_H


// I2C compartido por el INA219 y el OLED.
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// Botón BOOT de la placa ESP32, activo en bajo.
#define PIN_RESTABLECER_RED  0

#define DIR_INA219          0x40
#define DIR_OLED            0x3C

// HC-SR04 fijo, orientado hacia el frente.
#define PIN_US_TRIG      17
#define PIN_US_ECHO      16

// TB6612FNG, 2 motores CC. Canal A = rueda izquierda, B = derecha.
#define PIN_MOTOR_PWMA      25
#define PIN_MOTOR_AIN1      26
#define PIN_MOTOR_AIN2      27
#define PIN_MOTOR_PWMB      33
#define PIN_MOTOR_BIN1      32
#define PIN_MOTOR_BIN2      14
#define PIN_MOTOR_STBY      4

// Servos MG90S
#define PIN_SERVO_BRAZO_IZQ 18
#define PIN_SERVO_BRAZO_DER 19
#define PIN_SERVO_CUELLO    23

// LEDs indicadores: rojo = alerta, amarillo = operación normal.
#define PIN_LED_ROJO        13
#define PIN_LED_AMARILLO    2

#endif

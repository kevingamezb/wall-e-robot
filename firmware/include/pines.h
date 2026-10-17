// wall-e-robot/firmware/include/pines.h
// Kevin Gámez - 13/09/2026

#ifndef PINES_H
#define PINES_H

// Mapeo de pines (esquema de hardware) del robot; incluye también las
// direcciones I2C de los periféricos del bus compartido.

// I2C compartido por el INA219 y el OLED.
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// Direcciones I2C de los periféricos del bus.
#define DIR_INA219          0x40
#define DIR_OLED            0x3C

// HC-SR04 fijo mirando al frente: TRIG lanza el pulso, ECHO devuelve el eco.
#define PIN_US_TRIG      17
#define PIN_US_ECHO      16

// TB6612FNG, 2 motores CC. Canal A = rueda izquierda, B = derecha.
// PWMA/PWMB = velocidad (PWM); AIN1/AIN2 y BIN1/BIN2 = sentido de giro.
#define PIN_MOTOR_PWMA      25
#define PIN_MOTOR_AIN1      26
#define PIN_MOTOR_AIN2      27
#define PIN_MOTOR_PWMB      33
#define PIN_MOTOR_BIN1      32
#define PIN_MOTOR_BIN2      14
#define PIN_MOTOR_STBY      4    // HIGH habilita el driver

// Servos MG90S
#define PIN_SERVO_BRAZO_IZQ 18
#define PIN_SERVO_BRAZO_DER 19
#define PIN_SERVO_CUELLO    23

// LEDs indicadores: rojo = alerta, amarillo = operación normal.
#define PIN_LED_ROJO        13
#define PIN_LED_AMARILLO    2

#endif // PINES_H

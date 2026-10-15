// wall-e-robot/firmware/include/pines.h
// Kevin Gámez - 13/09/2026

#ifndef PINES_H
#define PINES_H

// Cableado físico del robot.

// I2C compartido por el INA219 y el OLED.
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

#define DIR_INA219          0x40   // sin puentes (valor de fábrica)
#define DIR_OLED            0x3C   // sin puentes (valor de fábrica)

// HC-SR04 fijo mirando al frente.
// TODO(hardware): el ECHO llega a 5 V; debe pasar por un divisor 1k/2k antes del GPIO.
#define PIN_US_TRIG      17
#define PIN_US_ECHO      16

// TB6612FNG, 2 motores CC. Canal A = rueda izquierda, B = derecha
#define PIN_MOTOR_PWMA      25
#define PIN_MOTOR_AIN1      26
#define PIN_MOTOR_AIN2      27
#define PIN_MOTOR_PWMB      33
#define PIN_MOTOR_BIN1      32
#define PIN_MOTOR_BIN2      14
#define PIN_MOTOR_STBY      4    // HIGH habilita el driver

// Servos MG90S: señal al GPIO, alimentación por el buck de 5 V.
#define PIN_SERVO_BRAZO_IZQ 18
#define PIN_SERVO_BRAZO_DER 19
#define PIN_SERVO_CUELLO    23

// LEDs indicadores (el verde de encendido va directo al riel de 5 V, sin GPIO).
#define PIN_LED_ROJO        13
#define PIN_LED_AMARILLO    2

#endif // PINES_H

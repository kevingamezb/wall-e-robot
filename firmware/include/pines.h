// wall-e-robot/firmware/include/pines.h
// Kevin Gámez - 13/09/2026

#ifndef PINES_H
#define PINES_H

// Cableado físico del robot. Todo lo que depende de dónde está
// conectado un cable vive aquí (o en config.h para lo lógico).

// I2C compartido (INA219 y OLED)
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// Direcciones I2C
#define DIR_INA219          0x40   // sin puentes (fábrica)
#define DIR_OLED            0x3C   // sin puentes (fábrica)

// Sensor de ultrasonido (HC-SR04), fijo mirando al frente
// ECHO sale a 5 V: pasa por un divisor 1k/2k antes del GPIO.
#define PIN_RADAR_TRIG      17
#define PIN_RADAR_ECHO      16

// Motores (driver TB6612FNG, 2 motores CC)
#define PIN_MOTOR_PWMA      25   // rueda izquierda: PWM
#define PIN_MOTOR_AIN1      26   // rueda izquierda: dirección
#define PIN_MOTOR_AIN2      27   // rueda izquierda: dirección
#define PIN_MOTOR_PWMB      33   // rueda derecha: PWM
#define PIN_MOTOR_BIN1      32   // rueda derecha: dirección
#define PIN_MOTOR_BIN2      14   // rueda derecha: dirección
#define PIN_MOTOR_STBY      4    // HIGH habilita el driver

// Servos MG90S (señal; alimentación por el buck de 5 V)
#define PIN_SERVO_BRAZO_IZQ 18
#define PIN_SERVO_BRAZO_DER 19
#define PIN_SERVO_CUELLO    23

// LEDs indicadores
// (el LED verde de encendido va directo al riel de 5 V, sin GPIO)
#define PIN_LED_ROJO        13
#define PIN_LED_AMARILLO    2

#endif // PINES_H

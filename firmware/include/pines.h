// wall-e-robot/firmware/include/pines.h
// Kevin Gámez - 13/09/2026

#ifndef PINES_H
#define PINES_H

// ============================================================
// Cableado físico del robot. Todo lo que depende de dónde está
// conectado un cable vive aquí (o en config.h para lo lógico).
// ============================================================

// --- I2C compartido (PCA9685, INA219, OLED si se conecta) ---
#define PIN_I2C_SDA         21
#define PIN_I2C_SCL         22

// Direcciones I2C
#define DIR_PCA9685         0x41   // puente A0 soldado (0x40 + 1). Ver notas.
#define DIR_INA219          0x40   // sin puentes (fábrica)

// --- Sensor de ultrasonido (HC-SR04), montado en el servo del radar ---
#define PIN_RADAR_TRIG      5
#define PIN_RADAR_ECHO      18

// --- Motores (driver L298N, 2 motores CC) ---
#define PIN_MOTOR_IN1       13
#define PIN_MOTOR_IN2       12
#define PIN_MOTOR_IN3       14
#define PIN_MOTOR_IN4       27
#define PIN_MOTOR_ENA       26
#define PIN_MOTOR_ENB       25

#endif // PINES_H
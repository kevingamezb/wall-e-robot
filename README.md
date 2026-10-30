# 🤖 Wall-E Robot (ESP32 + App de escritorio)

<p align="center">
  <img src="app/recursos/titulo.png" alt="Wall-E Robot" width="720">
</p>

<p align="center">El robot ESP32 autónomo de código abierto, controlado por WiFi desde una app de escritorio en Python.</p>

<p align="center">
  <a href="LICENSE"><img alt="Licencia: GPL v3" src="https://img.shields.io/badge/Licencia-GPLv3-blue.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-blue.svg">
  <img alt="PlatformIO" src="https://img.shields.io/badge/PlatformIO-ESP32-orange.svg">
</p>

---

Un robot Wall-E autónomo y controlado por WiFi basado en el chip **ESP32**. Cuenta con una
arquitectura desacoplada de software, una aplicación de escritorio interactiva y un sistema de
actualización inalámbrica (OTA).

---

<p align="center">
  <img src="app/recursos/foto_gui.png" alt="Wall-E Robot" width="680">
</p>

## ✨ Características principales

* **🧠 Navegación inteligente:** modo autónomo con bucle de control no bloqueante (`millis()`) y evasión de obstáculos.
* **💻 App de escritorio:** panel de control modular en Python (Tkinter); la conexión se abre en un hilo aparte para no congelar la GUI, con socket no bloqueante y refresco por eventos (`after`).
* **🎮 Control manual explícito:** botón **MODO** (manual/automático); el gamepad solo manda en manual.
* **📡 Telemetría en tiempo real:** comunicación bidireccional WiFi/TCP con mensajes JSON de una sola línea (`\n`).
* **⚡ Actualizaciones inalámbricas:** soporte OTA con validación MD5 y guardia de rollback.


## 📄 Licencia

Este proyecto está bajo la Licencia **GPL-3.0**. Consulta [`LICENSE`](LICENSE) para más detalles.

import base64
import http.client
import json


HOST_OTA = "192.168.4.1"
USUARIO_FABRICA = "walle"
CLAVE_FABRICA = "wall-e-ota"


def preparar_credenciales(wifi: str, usuario_ota: str, clave_ota: str) -> bytes:
    for nombre, valor in (("Wi-Fi", wifi), ("OTA", clave_ota)):
        if not 8 <= len(valor) <= 63 or not all(32 <= ord(c) <= 126 for c in valor):
            raise ValueError(f"La contraseña {nombre} debe tener entre 8 y 63 caracteres ASCII imprimibles.")
    if not 1 <= len(usuario_ota) <= 32 or not all(
        33 <= ord(c) <= 126 and c != ":" for c in usuario_ota
    ):
        raise ValueError("El usuario OTA debe tener entre 1 y 32 caracteres ASCII, sin espacios ni «:».")
    datos = {"wifi": wifi, "usuario_ota": usuario_ota, "clave_ota": clave_ota}
    return json.dumps(datos).encode("ascii")


def guardar_por_red(usuario_actual: str, clave_actual: str, mensaje: bytes):
    autorizacion = base64.b64encode(f"{usuario_actual}:{clave_actual}".encode()).decode("ascii")
    conexion = http.client.HTTPConnection(HOST_OTA, timeout=5)
    try:
        conexion.request("POST", "/credenciales", body=mensaje, headers={
            "Authorization": f"Basic {autorizacion}",
            "Content-Type": "application/json",
        })
        estado = conexion.getresponse().status
    except (OSError, http.client.HTTPException) as error:
        raise OSError("El ESP32 no confirmó el cambio. Comprueba la conexión a la red WALL-E.") from error
    finally:
        conexion.close()

    if estado != 204:
        errores = {
            400: "El ESP32 rechazó el formato de las nuevas credenciales.",
            401: "El Portal OTA rechazó el usuario o la contraseña actuales.",
            404: "El firmware instalado no permite cambiar las credenciales desde la app.",
            409: "El ESP32 está ocupado. Espera a que termine antes de volver a intentar.",
            500: "El ESP32 no pudo guardar las credenciales en su memoria.",
        }
        raise OSError(errores.get(estado, "El ESP32 devolvió una respuesta inesperada."))

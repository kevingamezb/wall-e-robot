// wall-e-robot/firmware/lib/ota/ota.cpp
// Kevin Gámez - 16/10/2026

#include "ota.h"

#include <WiFi.h>
#include <WebServer.h>
#include <Update.h>
#include <ArduinoOTA.h>
#include <esp_ota_ops.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "comunicacion.h"
#include "oled.h"
#include "bateria.h"
#include "distancia.h"

Ota ota;

// Servidor HTTP del portal OTA (solo se abre en iniciar()).
static WebServer servidorWeb(PUERTO_OTA_WEB);

// La tarea de guardia y el loop la comparten: volatile porque se lee desde
// la tarea de guardia.
static volatile bool s_confirmado = false;

// Estado de la subida web en curso: autorizada (autenticada) y completada.
static bool s_uploadAutorizado = false;
static bool s_uploadOk         = false;

// El portal queda abierto solo si no hay clave configurada.
static bool autenticado() {
    if (OTA_CLAVE[0] == '\0') {
        return true;
    }
    return servidorWeb.authenticate(OTA_USUARIO, OTA_CLAVE);
}


// --------------------------------------------------------------- self-test
bool Ota::selfTestInicial(String& motivo) {

    // Chequeos FATALES: si fallan, se revierte.
    if (WiFi.softAPIP() == INADDR_NONE) {
        motivo = "AP sin IP";
        return false;
    }

    if (!comunicacion.estaEscuchando()) {
        motivo = "servidor TCP no escucha";
        return false;
    }

    // Avisos: módulos habilitados que no inicializaron (hardware ausente o con
    // fallo). NO revierten: un periférico que no responde no es firmware roto.
    // Además, llegar hasta aquí ya implica que todos los iniciar() terminaron.
    if (MODULOS.oled && !oled.activo()) {
        Serial.println("[OTA] Aviso (no revierte): OLED habilitado sin inicializar.");
    }
    if (MODULOS.bateria && !bateria.activo()) {
        Serial.println("[OTA] Aviso (no revierte): bateria habilitada sin inicializar.");
    }
    if (MODULOS.distancia && !sensorDistancia.listo()) {
        Serial.println("[OTA] Aviso (no revierte): distancia habilitada sin inicializar.");
    }

    motivo = "ok";
    return true;
}


// ------------------------------------------------------------- rollback

// Tarea FreeRTOS de guardia: corre en paralelo al loop() y no depende de él,
// por eso protege también si setup() o loop() se cuelgan. Si la partición en
// ejecución está en PENDING_VERIFY y no se confirma en OTA_AUTOCONFIRMA_MS,
// la marca inválida y reinicia (rollback a la versión anterior).
static void tareaGuardiaRollback(void*) {

    const esp_partition_t* corriendo = esp_ota_get_running_partition();
    esp_ota_img_states_t   estado    = ESP_OTA_IMG_UNDEFINED;

    // Sin verificación pendiente: arranque normal, la tarea termina.
    if (esp_ota_get_state_partition(corriendo, &estado) != ESP_OK ||
        estado != ESP_OTA_IMG_PENDING_VERIFY) {

        Serial.println("[OTA] Arranque normal (sin verificacion pendiente).");
        vTaskDelete(NULL);
        return;
    }

    Serial.printf("[OTA] Version nueva pendiente de verificacion; "
                  "confirmo en <= %lu ms o revierto.\n",
                  (unsigned long)OTA_AUTOCONFIRMA_MS);

    uint32_t inicio = millis();
    while ((millis() - inicio) < OTA_AUTOCONFIRMA_MS) {
        if (s_confirmado) {
            Serial.println("[OTA] Confirmada a tiempo; rollback desarmado.");
            vTaskDelete(NULL);
            return;
        }
        vTaskDelay(pdMS_TO_TICKS(200));
    }

    Serial.println("[OTA] El self-test NO confirmo a tiempo: "
                   "REVIRTIENDO a la version anterior.");
    esp_err_t e = esp_ota_mark_app_invalid_rollback_and_reboot();
    Serial.printf("[OTA] No se pudo revertir (%s). Sigo en la version nueva.\n",
                  esp_err_to_name(e));
    vTaskDelete(NULL);
}


void Ota::iniciarGuardiaRollback() {
    xTaskCreate(tareaGuardiaRollback, "rollback", 8192, NULL, 1, NULL);
}


void Ota::confirmar() {

    s_confirmado = true;

    const esp_partition_t* corriendo = esp_ota_get_running_partition();
    esp_ota_img_states_t   estado    = ESP_OTA_IMG_UNDEFINED;

    if (esp_ota_get_state_partition(corriendo, &estado) == ESP_OK &&
        estado == ESP_OTA_IMG_PENDING_VERIFY) {

        esp_err_t e = esp_ota_mark_app_valid_cancel_rollback();
        Serial.printf("[OTA] Version confirmada en %s: %s\n",
                      corriendo ? corriendo->label : "?",
                      esp_err_to_name(e));
    }
}


void Ota::revertir() {
    Serial.println("[OTA] Revirtiendo manualmente...");
    s_confirmado = false;
    esp_ota_mark_app_invalid_rollback_and_reboot();
}


bool Ota::pendiente() const {

    const esp_partition_t* corriendo = esp_ota_get_running_partition();
    esp_ota_img_states_t   estado    = ESP_OTA_IMG_UNDEFINED;

    if (esp_ota_get_state_partition(corriendo, &estado) != ESP_OK) {
        return false;
    }
    return estado == ESP_OTA_IMG_PENDING_VERIFY;
}


// ------------------------------------------------------------------ web
static String paginaPrincipal() {

    String h;
    h += F("<!doctype html><html lang='es'><head><meta charset='utf-8'>");
    h += F("<meta name='viewport' content='width=device-width,initial-scale=1'>");
    h += F("<title>WALL-E OTA</title></head><body style='font-family:sans-serif;max-width:520px;margin:2rem auto'>");
    h += F("<h1>WALL-E &mdash; Actualizaci&oacute;n OTA</h1>");
    h += F("<p>Versi&oacute;n actual: <b>");
    h += PROYECTO_VERSION;
    h += F("</b></p>");
    if (ota.pendiente()) {
        h += F("<p style='color:#b00'><b>Estado:</b> pendiente de confirmaci&oacute;n (rollback armado)</p>");
    }
    h += F("<form method='POST' action='/update' enctype='multipart/form-data'>");
    h += F("<p>MD5 (32 hex, opcional):<br>"
          "<input type='text' name='md5' maxlength='32' size='36' placeholder='pegar MD5 del .bin'></p>");
    h += F("<p>Firmware .bin:<br><input type='file' name='firmware' accept='.bin' required></p>");
    h += F("<p><button type='submit'>Actualizar</button></p>");
    h += F("</form></body></html>");
    return h;
}


static String paginaResultado(bool ok, const String& mensaje) {

    String h;
    h += F("<!doctype html><html lang='es'><head><meta charset='utf-8'>");
    h += F("<meta name='viewport' content='width=device-width,initial-scale=1'>");
    h += F("<title>WALL-E OTA</title></head><body style='font-family:sans-serif;max-width:520px;margin:2rem auto'>");
    h += ok ? F("<h1 style='color:#080'>Actualizaci&oacute;n correcta</h1>")
            : F("<h1 style='color:#b00'>Error de actualizaci&oacute;n</h1>");
    h += F("<p>");
    h += mensaje;
    h += F("</p><p><a href='/'>Volver</a></p></body></html>");
    return h;
}


// GET /: sirve el formulario del portal (tras Basic Auth).
static void manejarRaiz() {

    if (!autenticado()) {
        servidorWeb.requestAuthentication();
        return;
    }
    servidorWeb.send(200, "text/html; charset=utf-8", paginaPrincipal());
}


// POST /update: recibe el cuerpo de la subida. Basic Auth antes de tocar la
// flash; el MD5 opcional (32 hex) se aplica a la imagen si se envió.
static void manejarUpload() {

    HTTPUpload& subida = servidorWeb.upload();

    esp_task_wdt_reset();   // la subida puede tardar: no dejar que el WDT corte

    if (subida.status == UPLOAD_FILE_START) {

        s_uploadAutorizado = false;
        s_uploadOk         = false;

        // Basic Auth ANTES de tocar la flash: si falla, se descarta el cuerpo.
        if (!autenticado()) {
            Serial.println("[OTA-WEB] Subida RECHAZADA: sin autenticacion.");
            return;
        }

        String md5 = servidorWeb.arg("md5");
        Serial.printf("[OTA-WEB] Inicio: '%s' (%u bytes) MD5=%s\n",
                      subida.filename.c_str(), (unsigned)subida.totalSize,
                      md5.length() ? md5.c_str() : "(ninguno)");

        if (!Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH)) {
            Update.printError(Serial);
            return;
        }
        if (md5.length() == 32) {
            Update.setMD5(md5.c_str());
        }
        s_uploadAutorizado = true;

    } else if (subida.status == UPLOAD_FILE_WRITE) {

        if (!s_uploadAutorizado) {
            return;
        }
        if (Update.write(subida.buf, subida.currentSize) != subida.currentSize) {
            Update.printError(Serial);
        }

    } else if (subida.status == UPLOAD_FILE_END) {

        if (!s_uploadAutorizado) {
            return;
        }
        if (Update.end(true)) {
            s_uploadOk = true;
            Serial.printf("[OTA-WEB] Imagen escrita: %u bytes.\n",
                          (unsigned)subida.totalSize);
        } else {
            Update.printError(Serial);
        }

    } else if (subida.status == UPLOAD_FILE_ABORTED) {
        Update.abort();
        s_uploadAutorizado = false;
        s_uploadOk         = false;
        Serial.println("[OTA-WEB] Subida abortada.");
    }
}


// POST /update: respuesta final al navegador. Si la imagen se aplicó bien,
// informa y reinicia para arrancar la versión nueva.
static void manejarUpdate() {

    if (!autenticado()) {
        servidorWeb.requestAuthentication();
        return;
    }

    bool ok = s_uploadOk && !Update.hasError();
    String mensaje = ok ? String("Firmware actualizado. Reiniciando...")
                        : String("No se pudo aplicar: ") + Update.errorString();

    servidorWeb.sendHeader("Connection", "close");
    servidorWeb.send(200, "text/html; charset=utf-8",
                     paginaResultado(ok, mensaje));

    if (ok) {
        Serial.println("[OTA-WEB] Reiniciando con la version nueva...");
        delay(300);
        ESP.restart();
    }
}


// Rutas del portal: formulario en /, subida en /update, 404 para el resto.
static void configurarWeb() {

    servidorWeb.on("/",            HTTP_GET,  manejarRaiz);
    servidorWeb.on("/update",      HTTP_POST, manejarUpdate, manejarUpload);
    servidorWeb.onNotFound([]() {
        servidorWeb.send(404, "text/plain", "No encontrado");
    });

    servidorWeb.begin();
    Serial.println("[OTA-WEB] Portal listo en http://192.168.4.1/");
}


// ArduinoOTA: mismo nombre de host y clave que el portal web.
static void configurarArduinoOta() {

    ArduinoOTA.setHostname(WIFI_AP_SSID);
    if (OTA_CLAVE[0] != '\0') {
        ArduinoOTA.setPassword(OTA_CLAVE);
    }

    ArduinoOTA.onStart([]() {
        Serial.println("[OTA] ArduinoOTA: inicio de subida.");
    });
    ArduinoOTA.onProgress([](unsigned int, unsigned int) {
        esp_task_wdt_reset();
    });
    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] ArduinoOTA: fin.");
    });
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("[OTA] ArduinoOTA error %u\n", (unsigned)error);
    });

    ArduinoOTA.begin();
    Serial.println("[OTA] ArduinoOTA listo (puerto 3232).");
}


void Ota::iniciar() {

    if (!OTA_ACTIVADO) {
        Serial.println("[OTA] Desactivado por configuracion.");
        return;
    }

    configurarWeb();
    configurarArduinoOta();
}


void Ota::procesar() {

    if (!OTA_ACTIVADO) {
        return;
    }

    ArduinoOTA.handle();
    servidorWeb.handleClient();
}

// wall-e-robot/firmware/test/test_decision/test_decision.cpp
// Kevin Gámez - 03/11/2026
//
// Pruebas nativas de la decisión autónoma (sin ESP32 ni hardware).
//   pio test -e native

#include <unity.h>

#include "decision.h"


void setUp() {}
void tearDown() {}


// ------------------------------------------------------- sin datos -> ALTO
void test_sin_lectura_fresca_se_detiene() {
    TEST_ASSERT_EQUAL(ManiobraDecision::ALTO,
                      decidirManiobra(false, 100.0f, 15.0f));
}

void test_sin_eco_se_detiene() {
    TEST_ASSERT_EQUAL(ManiobraDecision::ALTO,
                      decidirManiobra(true, -1.0f, 15.0f));
}

void test_distancia_negativa_se_detiene() {
    TEST_ASSERT_EQUAL(ManiobraDecision::ALTO,
                      decidirManiobra(true, -0.1f, 15.0f));
}


// --------------------------------------------------- obstáculo -> DERECHA
void test_obstaculo_cercano_gira() {
    TEST_ASSERT_EQUAL(ManiobraDecision::DERECHA,
                      decidirManiobra(true, 8.0f, 15.0f));
}

void test_borde_exacto_del_umbral_es_obstaculo() {
    TEST_ASSERT_EQUAL(ManiobraDecision::DERECHA,
                      decidirManiobra(true, 15.0f, 15.0f));
}

void test_distancia_cero_es_obstaculo() {
    TEST_ASSERT_EQUAL(ManiobraDecision::DERECHA,
                      decidirManiobra(true, 0.0f, 15.0f));
}


// ------------------------------------------------------ camino -> RECTO
void test_camino_libre_avanza() {
    TEST_ASSERT_EQUAL(ManiobraDecision::RECTO,
                      decidirManiobra(true, 15.1f, 15.0f));
}

void test_distancia_lejana_avanza() {
    TEST_ASSERT_EQUAL(ManiobraDecision::RECTO,
                      decidirManiobra(true, 120.0f, 15.0f));
}


// ------------------------------------------------------------ nombres
void test_nombres_para_telemetria() {
    TEST_ASSERT_EQUAL_STRING("alto",    nombreManiobra(ManiobraDecision::ALTO));
    TEST_ASSERT_EQUAL_STRING("recto",   nombreManiobra(ManiobraDecision::RECTO));
    TEST_ASSERT_EQUAL_STRING("derecha", nombreManiobra(ManiobraDecision::DERECHA));
}


int main(int, char**) {
    UNITY_BEGIN();

    RUN_TEST(test_sin_lectura_fresca_se_detiene);
    RUN_TEST(test_sin_eco_se_detiene);
    RUN_TEST(test_distancia_negativa_se_detiene);
    RUN_TEST(test_obstaculo_cercano_gira);
    RUN_TEST(test_borde_exacto_del_umbral_es_obstaculo);
    RUN_TEST(test_distancia_cero_es_obstaculo);
    RUN_TEST(test_camino_libre_avanza);
    RUN_TEST(test_distancia_lejana_avanza);
    RUN_TEST(test_nombres_para_telemetria);

    return UNITY_END();
}

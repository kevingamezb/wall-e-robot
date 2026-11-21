#include <unity.h>

#include "decision.h"

using Maniobra = ManiobraDecision;

void setUp() {}
void tearDown() {}

static DecisionAuto medir(NavegacionAuto& robot, uint32_t ahora, float cm,
                          uint32_t inicio, bool detenidos = true, bool fresca = true) {
    return robot.actualizar(ahora, detenidos, fresca, cm, inicio, 25.0f);
}

static void iniciarGiroDerecha(NavegacionAuto& robot) {
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 0, 80, 0).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::RECTO, medir(robot, 250, 80, 249).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 500, 25, 499, false).maniobra);
    TEST_ASSERT_EQUAL(GestoAuto::NINGUNO, medir(robot, 600, 25, 499, false).gesto);
    const auto pausa = medir(robot, 650, 25, 499);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, pausa.maniobra);
    TEST_ASSERT_EQUAL(GestoAuto::CUELLO_DERECHA, pausa.gesto);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1049, 25, 999).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::DERECHA, medir(robot, 1050, 25, 999).maniobra);
}

static void completarDosGiros(NavegacionAuto& robot) {
    iniciarGiroDerecha(robot);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1400, 25, 1250, false).maniobra);
    medir(robot, 1550, 25, 1500);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1560, 25, 1500).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::IZQUIERDA, medir(robot, 1750, 25, 1749).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::IZQUIERDA, medir(robot, 2449, 25, 2250, false).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 2450, 25, 2250, false).maniobra);
    medir(robot, 2600, 25, 2500);
}

void test_alterna_el_primer_giro_y_mide_despues_de_frenar() {
    NavegacionAuto robot;
    iniciarGiroDerecha(robot);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1400, 80, 1250, false).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1550, 80, 1500, false).maniobra);
    medir(robot, 1600, 80, 1500);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1610, 80, 1599).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::RECTO, medir(robot, 1800, 80, 1799).maniobra);
    medir(robot, 2050, 8, 2049);
    TEST_ASSERT_EQUAL(GestoAuto::CUELLO_IZQUIERDA, medir(robot, 2200, 8, 2049).gesto);
    TEST_ASSERT_EQUAL(Maniobra::IZQUIERDA, medir(robot, 2600, 8, 2549).maniobra);
}

void test_saluda_si_el_segundo_giro_despeja_el_camino() {
    NavegacionAuto robot;
    completarDosGiros(robot);
    const auto saludo = medir(robot, 2750, 80, 2749);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, saludo.maniobra);
    TEST_ASSERT_EQUAL(GestoAuto::SALUDO, saludo.gesto);
    TEST_ASSERT_EQUAL(GestoAuto::NINGUNO, medir(robot, 3100, 80, 3000).gesto);
    medir(robot, 3101, 80, 3000);
    TEST_ASSERT_EQUAL(Maniobra::RECTO, medir(robot, 3250, 80, 3249).maniobra);
}

void test_se_bloquea_tras_dos_giros_y_solo_sale_con_camino_libre() {
    NavegacionAuto robot;
    completarDosGiros(robot);
    TEST_ASSERT_TRUE(medir(robot, 2750, 8, 2749).bloqueado);
    TEST_ASSERT_TRUE(medir(robot, 3000, -1, 2999).bloqueado);
    TEST_ASSERT_TRUE(medir(robot, 3250, 80, 3249, true, false).bloqueado);
    const auto libre = medir(robot, 3500, 80, 3499);
    TEST_ASSERT_FALSE(libre.bloqueado);
    TEST_ASSERT_EQUAL(Maniobra::RECTO, libre.maniobra);
}

void test_perder_el_eco_interrumpe_el_giro_y_reiniciar_cancela_la_secuencia() {
    NavegacionAuto robot;
    iniciarGiroDerecha(robot);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1250, -1, 1249, false).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1400, -1, 1249).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1500, 8, 1499, true, false).maniobra);
    robot.reiniciar();
    medir(robot, 1600, 8, 1499);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1650, 8, 1599).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 1750, 8, 1749).maniobra);
    TEST_ASSERT_EQUAL(GestoAuto::CUELLO_IZQUIERDA, medir(robot, 1751, 8, 1749).gesto);
}

void test_acepta_mediciones_despues_del_desbordamiento_de_millis() {
    NavegacionAuto robot;
    medir(robot, UINT32_MAX - 1, 80, UINT32_MAX - 2);
    TEST_ASSERT_EQUAL(Maniobra::ALTO, medir(robot, 5, 80, UINT32_MAX - 2).maniobra);
    TEST_ASSERT_EQUAL(Maniobra::RECTO, medir(robot, 6, 80, 2).maniobra);
}

void test_nombres_para_telemetria() {
    TEST_ASSERT_EQUAL_STRING("alto",      nombreManiobra(Maniobra::ALTO));
    TEST_ASSERT_EQUAL_STRING("recto",     nombreManiobra(Maniobra::RECTO));
    TEST_ASSERT_EQUAL_STRING("derecha",   nombreManiobra(Maniobra::DERECHA));
    TEST_ASSERT_EQUAL_STRING("izquierda", nombreManiobra(Maniobra::IZQUIERDA));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_alterna_el_primer_giro_y_mide_despues_de_frenar);
    RUN_TEST(test_saluda_si_el_segundo_giro_despeja_el_camino);
    RUN_TEST(test_se_bloquea_tras_dos_giros_y_solo_sale_con_camino_libre);
    RUN_TEST(test_perder_el_eco_interrumpe_el_giro_y_reiniciar_cancela_la_secuencia);
    RUN_TEST(test_acepta_mediciones_despues_del_desbordamiento_de_millis);
    RUN_TEST(test_nombres_para_telemetria);
    return UNITY_END();
}

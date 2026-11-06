"""Pruebas de extremo a extremo del dispatcher (POST /api).

Recorren el ciclo completo contra la BD real cuando esta disponible:
ingreso de sesion, registro publico de estudiante, perfil de
configuracion, guardado y borrado de foto, modulo de simulacion y el
limitador publico (429). Cuando MariaDB no esta disponible, toda la
suite se omite con un mensaje claro.
"""

import uuid

import pytest

from app.limites import limitador_publico

from helpers import obtener_token, pedir, REQUIERE_BD

pytestmark = REQUIERE_BD

FOTO_PNG_1PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def _limitador_fresco():
    """Cada prueba empieza con buckets vacios: el limitador por proceso
    compartido con el dispatcher no contamina pruebas previas."""
    limitador_publico.reiniciar()
    yield
    limitador_publico.reiniciar()

FOTO_PNG_1PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def llamar(cliente, accion, datos=None, token=None):
    respuesta = cliente.post("/api", json=pedir(accion, datos, token))
    cuerpo = respuesta.json()
    return respuesta, cuerpo


def ingresar(cliente, credenciales, rol):
    respuesta, cuerpo = llamar(
        cliente,
        "iniciar_sesion",
        credenciales[rol],
    )
    assert respuesta.status_code == 200 and cuerpo["ok"], cuerpo
    return obtener_token(respuesta), cuerpo["datos"]


# --- sesion -----------------------------------------------------------

def test_iniciar_sesion_declina_credenciales_invalidas(cliente, credenciales):
    respuesta, cuerpo = llamar(
        cliente,
        "iniciar_sesion",
        {"correo": credenciales["estudiante"]["correo"], "contrasena": "incorrecta"},
    )
    assert respuesta.status_code == 401
    assert cuerpo["ok"] is False
    assert "mensaje" in cuerpo


def test_iniciar_sesion_y_accion_protegida(cliente, credenciales):
    token, datos = ingresar(cliente, credenciales, "estudiante")
    assert datos["usuario"]["rol"] == "estudiante"
    assert isinstance(datos["modulos"], list)
    assert isinstance(datos["no_leidas"], int)

    respuesta, cuerpo = llamar(cliente, "sesion_consultar", token=token)
    assert respuesta.status_code == 200
    assert cuerpo["datos"]["usuario"]["correo"] == credenciales["estudiante"][
        "correo"
    ]


def test_accion_protegida_sin_token_pide_sesion(cliente):
    respuesta, cuerpo = llamar(cliente, "sesion_consultar")
    assert respuesta.status_code == 401
    assert cuerpo["ok"] is False


def test_accion_inexistente_da_404(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "estudiante")
    respuesta, cuerpo = llamar(cliente, "accion_que_no_existe", token=token)
    assert respuesta.status_code == 404
    assert cuerpo["ok"] is False


# --- registro publico --------------------------------------------------

def test_registro_estudiante_crea_cuenta_e_ingresa_automaticamente(cliente):
    sufijo = uuid.uuid4().hex[:10]
    datos = {
        "nombre": "Prueba de Registro",
        "correo": f"prueba.{sufijo}@ucc.edu.co",
        "telefono": "+57 300 000 0000",
        "programa": "Ingeniería de Software",
        "semestre": 3,
        "contrasena": "Registro2026bbb",
        "confirmacion_contrasena": "Registro2026bbb",
    }
    respuesta, cuerpo = llamar(cliente, "registrarse_estudiante", datos)
    assert respuesta.status_code == 200, cuerpo
    assert cuerpo["datos"]["usuario"]["rol"] == "estudiante"
    assert cuerpo["datos"]["nueva_cuenta"] is True
    token = obtener_token(respuesta)
    assert token

    # La sesion ya esta activa: la accion protegida responde al momento.
    respuesta_perfil, cuerpo_perfil = llamar(
        cliente, "perfil_obtener", token=token
    )
    assert respuesta_perfil.status_code == 200
    assert cuerpo_perfil["datos"]["usuario"]["nombre"] == "Prueba de Registro"

    # El correo queda tomado: el mismo registro vuelve a 409.
    respuesta_duplicado, cuerpo_duplicado = llamar(
        cliente, "registrarse_estudiante", datos
    )
    assert respuesta_duplicado.status_code == 409
    assert cuerpo_duplicado["ok"] is False


def test_registro_valida_campos_requeridos(cliente):
    respuesta, cuerpo = llamar(
        cliente,
        "registrarse_estudiante",
        {
            "nombre": "Semestre fuera de rango",
            "correo": f"invalido.{uuid.uuid4().hex[:6]}@ucc.edu.co",
            "programa": "Psicología",
            "semestre": 12,
            "contrasena": "Registro2026bbb",
            "confirmacion_contrasena": "Registro2026bbb",
        },
    )
    assert respuesta.status_code == 400
    assert cuerpo["ok"] is False


# --- perfil / configuracion -------------------------------------------

def test_perfil_obtener_y_guardar_datos_contacto(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "profesor")
    sufijo = uuid.uuid4().hex[:8]

    respuesta, cuerpo = llamar(cliente, "perfil_obtener", token=token)
    assert respuesta.status_code == 200
    assert cuerpo["datos"]["correo_institucional"] == credenciales["profesor"]["correo"]
    assert "tiene_foto" in cuerpo["datos"]

    respuesta_guardado, cuerpo_guardado = llamar(
        cliente,
        "perfil_guardar",
        {"telefono": "+57 601 555 0102", "correo_alternativo": f"prof.{sufijo}@gmail.com"},
        token=token,
    )
    assert respuesta_guardado.status_code == 200, cuerpo_guardado
    assert (
        cuerpo_guardado["datos"]["telefono"] == "+57 601 555 0102"
    )
    correo_alt = cuerpo_guardado["datos"]["correo_alternativo"]
    assert correo_alt == f"prof.{sufijo}@gmail.com"

    respuesta_no_leida, cuerpo_no_leida = llamar(
        cliente, "perfil_obtener", token=token
    )
    assert cuerpo_no_leida["datos"]["telefono"] == "+57 601 555 0102"


def test_perfil_rechaza_correo_alternativo_igual_al_institucional(
    cliente, credenciales
):
    token, _ = ingresar(cliente, credenciales, "profesor")
    respuesta, cuerpo = llamar(
        cliente,
        "perfil_guardar",
        {
            "correo_alternativo": credenciales["profesor"]["correo"],
        },
        token=token,
    )
    assert respuesta.status_code == 400
    assert cuerpo["ok"] is False


def test_perfil_foto_ciclo_completo_guardar_leer_borrar(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "monitor")

    respuesta, cuerpo = llamar(
        cliente,
        "perfil_guardar_foto",
        {"foto": FOTO_PNG_1PX},
        token=token,
    )
    assert respuesta.status_code == 200, cuerpo
    assert cuerpo["datos"]["tiene_foto"] is True
    assert cuerpo["datos"]["foto"] == FOTO_PNG_1PX

    respuesta_lectura, cuerpo_lectura = llamar(
        cliente, "perfil_obtener", token=token
    )
    assert cuerpo_lectura["datos"]["tiene_foto"] is True
    assert cuerpo_lectura["datos"]["foto"] == FOTO_PNG_1PX

    respuesta_borrado, cuerpo_borrado = llamar(
        cliente, "perfil_guardar_foto", {"foto": ""}, token=token
    )
    assert respuesta_borrado.status_code == 200
    assert cuerpo_borrado["datos"]["tiene_foto"] is False
    assert cuerpo_borrado["datos"]["foto"] == ""


def test_perfil_foto_rechaza_formato_invalido(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "monitor")
    respuesta, cuerpo = llamar(
        cliente,
        "perfil_guardar_foto",
        {"foto": "data:image/gif;base64,R0lGOD"},
        token=token,
    )
    assert respuesta.status_code == 400
    assert cuerpo["ok"] is False


# --- simulacion ---------------------------------------------------------

PARAMETROS_FIJOS = {
    "num_monitores": 2,
    "llegadas_diarias": 16,
    "duracion_media_horas": 1.5,
    "dias_simulados": 7,
    "repeticiones": 2,
    "semilla": 123,
}


def test_simulacion_api_es_determinista(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "admin")
    respuesta_uno, cuerpo_uno = llamar(
        cliente, "simulacion_ejecutar", PARAMETROS_FIJOS, token=token
    )
    respuesta_dos, cuerpo_dos = llamar(
        cliente, "simulacion_ejecutar", PARAMETROS_FIJOS, token=token
    )
    assert respuesta_uno.status_code == 200 == respuesta_dos.status_code
    assert cuerpo_uno["datos"]["resumen"] == cuerpo_dos["datos"]["resumen"]
    assert cuerpo_uno["datos"]["histograma"] == cuerpo_dos["datos"]["histograma"]
    assert "comparacion" in cuerpo_uno["datos"]


def test_simulacion_comparar_devuelve_cuatro_niveles(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "admin")
    respuesta, cuerpo = llamar(
        cliente, "simulacion_comparar", PARAMETROS_FIJOS, token=token
    )
    assert respuesta.status_code == 200
    comparacion = cuerpo["datos"]["comparacion"]
    assert [fila["num_monitores"] for fila in comparacion] == [1, 2, 3, 4]
    assert comparacion[0]["espera_media_horas"] >= comparacion[-1][
        "espera_media_horas"
    ]


def test_simulacion_valida_parametros(cliente, credenciales):
    token, _ = ingresar(cliente, credenciales, "admin")
    respuesta, cuerpo = llamar(
        cliente,
        "simulacion_ejecutar",
        dict(PARAMETROS_FIJOS, num_monitores=0),
        token=token,
    )
    assert respuesta.status_code == 400
    assert cuerpo["ok"] is False


@pytest.mark.parametrize("rol", ["estudiante", "monitor", "profesor", "bienestar", "asesoria"])
def test_simulacion_reservada_a_admin_rechaza_otros_roles(cliente, credenciales, rol):
    token, _ = ingresar(cliente, credenciales, rol)
    respuesta, cuerpo = llamar(
        cliente, "simulacion_ejecutar", PARAMETROS_FIJOS, token=token
    )
    assert respuesta.status_code == 403
    assert cuerpo["ok"] is False


def test_simulacion_menu_solo_admin_tiene_modulo(cliente, credenciales):
    """La vista Backoffice carga simulacion solo en el menu del admin."""
    _, datos_admin = ingresar(cliente, credenciales, "admin")
    claves_admin = {m["clave"] for m in datos_admin["modulos"]}
    _, datos_prof = ingresar(cliente, credenciales, "profesor")
    claves_prof = {m["clave"] for m in datos_prof["modulos"]}
    assert "simulacion" in claves_admin
    assert "simulacion" not in claves_prof


# --- limites publico ------------------------------------------------------

def test_limitador_publico_responde_429_en_disparo(cliente):
    limitador_publico.reiniciar()
    for _ in range(10):
        llamar(cliente, "iniciar_sesion", {"correo": "x@x.com", "contrasena": "no"})
    respuesta, cuerpo = llamar(
        cliente, "iniciar_sesion", {"correo": "x@x.com", "contrasena": "no"}
    )
    assert respuesta.status_code == 429
    assert cuerpo["ok"] is False
    limitador_publico.reiniciar()

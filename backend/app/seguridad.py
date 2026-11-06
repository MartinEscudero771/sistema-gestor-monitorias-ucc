import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .base_datos import consultar_uno, ejecutar
from .configuracion import (
    DURACION_SESION_HORAS,
    DURACION_TOKEN_ACCESO_MINUTOS,
    SECRETO_JWT,
)
from .errores import ErrorAplicacion
from .utilidades import (
    fecha_utc_actual,
    fecha_utc_con_horas,
)

ALGORITMO_JWT = "HS256"
EMISOR_JWT = "ucc-monitorias"
AUDIENCIA_JWT = "ucc-monitorias-web"

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)
_hash_falso = _hasher.hash(secrets.token_urlsafe(24))


def normalizar_correo(correo):
    return str(correo or "").strip().lower()


def hash_token(token):
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def generar_hash_contrasena(contrasena):
    return _hasher.hash(contrasena)


def necesita_rehash(hash_guardado):
    if not hash_guardado or not hash_guardado.startswith("$argon2"):
        return True
    try:
        return _hasher.check_needs_rehash(hash_guardado)
    except InvalidHashError:
        return True


def verificar_contrasena(contrasena, hash_guardado):
    if not hash_guardado:
        try:
            _hasher.verify(_hash_falso, contrasena)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        return False
    if hash_guardado.startswith("$argon2"):
        try:
            _hasher.verify(hash_guardado, contrasena)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
    return False


def buscar_usuario_por_correo(correo):
    return consultar_uno(
        """
        SELECT id_usuario, correo, nombre, hash_contrasena, rol, id_perfil,
               activo, telefono, correo_alternativo, foto_perfil
        FROM usuarios
        WHERE correo = %s
        """,
        (normalizar_correo(correo),),
    )


def actualizar_hash_contrasena(id_usuario, contrasena):
    ejecutar(
        "UPDATE usuarios SET hash_contrasena = %s WHERE id_usuario = %s",
        (generar_hash_contrasena(contrasena), id_usuario),
    )


def _codificar_jwt(carga):
    return jwt.encode(carga, SECRETO_JWT, algorithm=ALGORITMO_JWT)


def _decodificar_jwt(token):
    try:
        return jwt.decode(
            token,
            SECRETO_JWT,
            algorithms=[ALGORITMO_JWT],
            audience=AUDIENCIA_JWT,
            issuer=EMISOR_JWT,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as error:
        raise ErrorAplicacion("La credencial de acceso expiró.", 401) from error
    except jwt.InvalidTokenError as error:
        raise ErrorAplicacion("La credencial de acceso no es válida.", 401) from error


def expedir_token_acceso(id_sesion, usuario):
    return _crear_token_acceso(id_sesion, usuario)


def _crear_token_acceso(id_sesion, usuario):
    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(minutes=DURACION_TOKEN_ACCESO_MINUTOS)
    carga = {
        "sub": usuario["id_usuario"],
        "sid": id_sesion,
        "rol": usuario["rol"],
        "tipo": "acceso",
        "jti": secrets.token_urlsafe(32),
        "nonce": secrets.token_urlsafe(18),
        "iss": EMISOR_JWT,
        "aud": AUDIENCIA_JWT,
        "iat": int(ahora.timestamp()),
        "exp": int(expiracion.timestamp()),
    }
    return _codificar_jwt(carga), expiracion.strftime("%Y-%m-%dT%H:%M:%SZ")


def crear_sesion(usuario, ip_hash, agente_hash):
    id_sesion = "ses_" + secrets.token_urlsafe(18)
    token_refresco = secrets.token_urlsafe(48)
    fecha_expiracion = fecha_utc_con_horas(DURACION_SESION_HORAS)
    ahora = fecha_utc_actual()
    token, expira_en = _crear_token_acceso(id_sesion, usuario)
    ejecutar(
        """
        INSERT INTO sesiones
        (id_sesion, id_usuario, hash_refresh, fecha_creacion,
         fecha_expiracion, ultima_actividad, ip_hash, agente_hash, revocada)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
        """,
        (
            id_sesion,
            usuario["id_usuario"],
            hash_token(token_refresco),
            ahora,
            fecha_expiracion,
            ahora,
            ip_hash,
            agente_hash,
        ),
    )
    limpiar_datos_seguridad()
    return {
        "id_sesion": id_sesion,
        "token": token,
        "expira_en": expira_en,
        "token_refresco": token_refresco,
        "refresh_expira_en": fecha_expiracion,
    }


def _usuario_por_id(id_usuario):
    return consultar_uno(
        """
        SELECT id_usuario, correo, nombre, rol, id_perfil, activo,
               telefono, correo_alternativo, foto_perfil
        FROM usuarios
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )


def _sesion_activa(id_sesion):
    return consultar_uno(
        """
        SELECT id_sesion, id_usuario, hash_refresh, fecha_expiracion,
               ip_hash, agente_hash, revocada
        FROM sesiones
        WHERE id_sesion = %s
        """,
        (id_sesion,),
    )


def validar_token_acceso(token):
    # Uso local: se valida firma, vigencia y que la sesion siga activa.
    carga = _decodificar_jwt(token)
    if carga.get("tipo") != "acceso":
        raise ErrorAplicacion("La credencial de acceso no es válida.", 401)
    sesion = _sesion_activa(carga.get("sid"))
    if not sesion or int(sesion["revocada"]) == 1:
        raise ErrorAplicacion("La sesión no está activa.", 401)
    if sesion["fecha_expiracion"] <= fecha_utc_actual():
        raise ErrorAplicacion("La sesión expiró.", 401)
    usuario = _usuario_por_id(sesion["id_usuario"])
    if not usuario or int(usuario["activo"]) != 1:
        revocar_sesion(sesion["id_sesion"])
        raise ErrorAplicacion("El usuario no está activo.", 401)

    ejecutar(
        "UPDATE sesiones SET ultima_actividad = %s WHERE id_sesion = %s",
        (fecha_utc_actual(), sesion["id_sesion"]),
    )
    return sesion, usuario


def renovar_sesion(token_refresco):
    if not token_refresco:
        raise ErrorAplicacion("No hay una sesión para renovar.", 401)
    hash_actual = hash_token(token_refresco)
    sesion = consultar_uno(
        "SELECT * FROM sesiones WHERE hash_refresh = %s",
        (hash_actual,),
    )
    if not sesion or int(sesion["revocada"]) == 1:
        raise ErrorAplicacion("La sesión no está activa.", 401)
    if sesion["fecha_expiracion"] <= fecha_utc_actual():
        raise ErrorAplicacion("La sesión expiró.", 401)
    usuario = _usuario_por_id(sesion["id_usuario"])
    if not usuario or int(usuario["activo"]) != 1:
        revocar_sesion(sesion["id_sesion"])
        raise ErrorAplicacion("El usuario no está activo.", 401)

    token_refresco_nuevo = secrets.token_urlsafe(48)
    filas = ejecutar(
        """
        UPDATE sesiones
        SET hash_refresh = %s, ultima_actividad = %s
        WHERE id_sesion = %s AND hash_refresh = %s AND revocada = 0
        """,
        (
            hash_token(token_refresco_nuevo),
            fecha_utc_actual(),
            sesion["id_sesion"],
            hash_actual,
        ),
    )
    if filas != 1:
        raise ErrorAplicacion("La sesión ya fue renovada.", 401)
    token, expira_en = _crear_token_acceso(sesion["id_sesion"], usuario)
    return {
        "sesion": sesion,
        "usuario": usuario,
        "token": token,
        "expira_en": expira_en,
        "token_refresco": token_refresco_nuevo,
        "refresh_expira_en": sesion["fecha_expiracion"],
    }


def revocar_sesion(id_sesion):
    ejecutar(
        "UPDATE sesiones SET revocada = 1 WHERE id_sesion = %s",
        (id_sesion,),
    )


def revocar_sesiones_usuario(id_usuario):
    ejecutar(
        "UPDATE sesiones SET revocada = 1 WHERE id_usuario = %s AND revocada = 0",
        (id_usuario,),
    )


def limpiar_datos_seguridad():
    ejecutar(
        "DELETE FROM sesiones WHERE fecha_expiracion < %s",
        (fecha_utc_con_horas(-24),),
    )

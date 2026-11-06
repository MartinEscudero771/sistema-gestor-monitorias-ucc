import json
import logging

from .base_datos import consultar_todos, consultar_uno, ejecutar
from .utilidades import fecha_utc_actual

_registrador = logging.getLogger(__name__)


def registrar_auditoria(
    accion,
    resultado,
    id_usuario=None,
    id_usuario_objetivo=None,
    id_solicitud=None,
    direccion_ip=None,
    agente=None,
    detalle=None,
):
    try:
        if isinstance(detalle, (dict, list)):
            detalle_texto = json.dumps(detalle, ensure_ascii=False, default=str)
        elif detalle is None:
            detalle_texto = None
        else:
            detalle_texto = str(detalle)
        ejecutar(
            """
            INSERT INTO auditoria
            (id_usuario, id_usuario_objetivo, accion, resultado,
             id_solicitud, direccion_ip, agente, detalle, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_usuario,
                id_usuario_objetivo,
                str(accion)[:80],
                str(resultado)[:20],
                str(id_solicitud)[:80] if id_solicitud else None,
                str(direccion_ip)[:64] if direccion_ip else None,
                str(agente)[:255] if agente else None,
                detalle_texto,
                fecha_utc_actual(),
            ),
        )
    except Exception:
        _registrador.exception("No fue posible registrar el evento de auditoría.")


def listar_auditoria(
    accion=None,
    resultado=None,
    id_usuario=None,
    busqueda=None,
    desde=None,
    hasta=None,
    pagina=1,
    por_pagina=50,
):
    try:
        pagina = max(1, int(pagina))
    except (TypeError, ValueError):
        pagina = 1
    try:
        por_pagina = min(100, max(1, int(por_pagina)))
    except (TypeError, ValueError):
        por_pagina = 50
    condiciones = []
    parametros = []

    if accion:
        condiciones.append("accion = %s")
        parametros.append(str(accion).strip()[:80])
    if resultado:
        condiciones.append("resultado = %s")
        parametros.append(str(resultado).strip()[:20])
    if id_usuario:
        condiciones.append("(id_usuario = %s OR id_usuario_objetivo = %s)")
        parametros.extend([str(id_usuario).strip()[:40], str(id_usuario).strip()[:40]])
    if busqueda:
        termino = f"%{str(busqueda).strip()[:120]}%"
        condiciones.append(
            "(id_solicitud LIKE %s OR accion LIKE %s OR detalle LIKE %s)"
        )
        parametros.extend([termino, termino, termino])
    if desde:
        condiciones.append("fecha_creacion >= %s")
        parametros.append(str(desde))
    if hasta:
        condiciones.append("fecha_creacion <= %s")
        parametros.append(str(hasta))

    clausula = ""
    if condiciones:
        clausula = " WHERE " + " AND ".join(condiciones)

    total = consultar_uno(
        f"SELECT COUNT(*) AS total FROM auditoria{clausula}",
        tuple(parametros),
    )
    total_elementos = total["total"] if total else 0
    desplazamiento = (pagina - 1) * por_pagina
    elementos = consultar_todos(
        f"""
        SELECT id_auditoria, id_usuario, id_usuario_objetivo, accion,
               resultado, id_solicitud, direccion_ip, agente, detalle,
               fecha_creacion
        FROM auditoria{clausula}
        ORDER BY id_auditoria DESC
        LIMIT %s OFFSET %s
        """,
        tuple(parametros + [por_pagina, desplazamiento]),
    )
    paginas = max(1, (total_elementos + por_pagina - 1) // por_pagina)
    return {
        "total": total_elementos,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "paginas": paginas,
        "elementos": elementos,
    }

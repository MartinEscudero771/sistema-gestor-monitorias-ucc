"""Reporte oficial de monitorías.

Fuente única de verdad para el reporte. Lo consumen:
- backend/app/api.py (dispatcher POST /api, acción reportes_*)
- backend/app/rutas_extra.py (aliases REST GET /api/reportes/*)
No duplicar consultas en otros archivos.
"""

from decimal import Decimal

from ..base_datos import consultar_todos
from ..errores import ErrorAplicacion

ROLES_REPORTE = ("bienestar", "asesoria", "admin", "profesor")


def _exigir_rol(usuario):
    if usuario["rol"] not in ROLES_REPORTE:
        raise ErrorAplicacion("No tiene permiso para ver reportes.", 403)


def _numero(valor):
    """MySQL devuelve Decimal en SUM(); JSON necesita int/float."""
    if isinstance(valor, Decimal):
        if valor == int(valor):
            return int(valor)
        return float(valor)
    if isinstance(valor, float):
        return valor
    if isinstance(valor, int):
        return valor
    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return float(valor)
        except (TypeError, ValueError):
            return 0


def obtener_horas_por_monitor(usuario, datos=None, token_sesion=None):
    """Horas acumuladas (no rechazadas) por monitor activo."""
    _exigir_rol(usuario)
    filas = consultar_todos(
        """
        SELECT monitor.id_monitor, estudiante.nombre AS monitor,
               monitor.asignatura,
               COALESCE(SUM(informe.cantidad_horas), 0) AS horas,
               COUNT(informe.id_informe) AS informes
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        LEFT JOIN informes_horas AS informe
            ON informe.id_monitor = monitor.id_monitor
           AND informe.estado <> 'rechazado'
        WHERE monitor.estado = 'activo'
        GROUP BY monitor.id_monitor, estudiante.nombre, monitor.asignatura
        ORDER BY horas DESC
        """
    )
    for fila in filas:
        fila["horas"] = _numero(fila["horas"])
        fila["informes"] = _numero(fila["informes"])
    return {"filas": filas, "total": len(filas)}


def obtener_monitorias_por_asignatura(usuario, datos=None, token_sesion=None):
    """Conteo de monitorías agrupado por asignatura y estado."""
    _exigir_rol(usuario)
    filas = consultar_todos(
        """
        SELECT asignatura, COUNT(*) AS total,
               SUM(CASE WHEN estado = 'programada' THEN 1 ELSE 0 END) AS programadas,
               SUM(CASE WHEN estado = 'realizada' THEN 1 ELSE 0 END) AS realizadas,
               SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) AS canceladas
        FROM monitorias
        GROUP BY asignatura
        ORDER BY total DESC
        """
    )
    for fila in filas:
        fila["total"] = _numero(fila["total"])
        fila["programadas"] = _numero(fila["programadas"])
        fila["realizadas"] = _numero(fila["realizadas"])
        fila["canceladas"] = _numero(fila["canceladas"])
    return {"filas": filas}


def obtener_solicitudes_por_estado(usuario, datos=None, token_sesion=None):
    """Conteo de solicitudes de monitoría agrupado por estado."""
    _exigir_rol(usuario)
    filas = consultar_todos(
        """
        SELECT estado, COUNT(*) AS total
        FROM solicitudes_monitoria
        GROUP BY estado
        """
    )
    for fila in filas:
        fila["total"] = _numero(fila["total"])
    return {"filas": filas}

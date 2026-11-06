from datetime import date, datetime, timedelta, timezone


def fecha_utc_actual():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fecha_utc_con_horas(horas):
    fecha_futura = datetime.now(timezone.utc) + timedelta(hours=horas)
    return fecha_futura.strftime("%Y-%m-%dT%H:%M:%SZ")


def fecha_hoy_texto():
    return date.today().isoformat()


def fecha_con_dias(dias):
    return (date.today() + timedelta(days=dias)).isoformat()


def formatear_fecha(fecha_texto):
    try:
        fecha = date.fromisoformat(fecha_texto)
        return fecha.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return fecha_texto or ""


def formatear_hora(hora_texto):
    try:
        hora = datetime.strptime(hora_texto, "%H:%M")
        return hora.strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError):
        return hora_texto or ""


def formatear_fecha_hora(fecha_texto):
    try:
        fecha = datetime.strptime(fecha_texto, "%Y-%m-%dT%H:%M:%SZ")
        return fecha.strftime("%d/%m/%Y %I:%M %p")
    except (ValueError, TypeError):
        return fecha_texto or ""

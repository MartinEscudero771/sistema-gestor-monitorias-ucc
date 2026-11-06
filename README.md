# Sistema de Gestor de Monitorías Académicas UCC

<div align="center">

<img src=".github/assets/banner.svg" alt="Sistema de Gestor de Monitorías Académicas UCC — banner" width="1000">

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white&style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white&style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL%20%2F%20MariaDB-4479A1?logo=mysql&logoColor=white&style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript&logoColor=black&style=flat-square)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?logo=bootstrap&logoColor=white&style=flat-square)
![pytest](https://img.shields.io/badge/tests-77%20pasando-2EA043?logo=pytest&logoColor=white&style=flat-square)
![Licencia](https://img.shields.io/badge/licencia-MIT-CAD400?style=flat-square)
![Windows](https://img.shields.io/badge/uso%20local-Windows-0078D4?logo=windows11&logoColor=white&style=flat-square)

**App web Full Stack local** para coordinar el acompañamiento académico entre estudiantes,
monitores, profesores, Bienestar Universitario, Asesoría y Administración.
Incluye **registro público de estudiantes**, **configuración con foto/webcam**,
**simulador de capacidad M/G/c** (módulo Admin) y **auditoría completa**.

[Características](#módulos-y-crud) · [Instalación](#instalación) · [Pruebas](#pruebas) · [Documentación](#documentación) · [Licencia](#licencia)

</div>

---

## Problema
Las monitorías se coordinaban por chats y planillas: solicitudes perdidas, horas sin validar y estudiantes en riesgo sin seguimiento trazable.

## Descripción
App web Full Stack local que centraliza solicitudes, postulaciones a monitor, listas de riesgo, tutorías, informes de horas, calendario, notificaciones y reporte oficial. Roles: Estudiante, Monitor, Profesor, Bienestar, Asesoría, Admin (supervisión + auditoría).

## Tecnologías
Python 3.10+, FastAPI, Uvicorn, MySQL/MariaDB (PyMySQL), PyJWT, Argon2, python-dotenv, pytest + httpx (pruebas). Frontend: HTML5 semántico, CSS propio + Bootstrap local, JavaScript + Fetch, FullCalendar, getUserMedia (webcam).

## Arquitectura (MVC adaptado + POO)
| Capa | Implementación |
|---|---|
| Modelo | `backend/app/esquema.sql`, `backend/app/base_datos.py` (parametrizado), `backend/app/repositorio.py` (patrón Repositorio) |
| Vista | `frontend/index.html`, `css/estilos.css`, `js/` |
| Controlador | `backend/app/api.py`, `backend/app/modulos/*.py`, `validaciones.py`, `errores.py`, `limites.py`, `rutas_extra.py` |

Menú (`modulos/menu.py`): `clave` carga `window.vistas_ucc[clave]` (`aplicacion.js`); `accion` es la referencia del dispatcher. Arquitectura en [`docs/diagramas/arquitectura.png`](docs/diagramas/arquitectura.png) (fuente: [`docs/diagramas/arquitectura.puml`](docs/diagramas/arquitectura.puml)).

## Iteración 2 — POO, simulación y autonomía del estudiante
- **POO real:** `errores.py` (jerarquía de errores con código HTTP por subclase), `repositorio.py` (`Repositorio`/`RepositorioUsuarios` con lista blanca de columnas), `limites.py` (`LimitadorPeticiones`, ventana deslizante, activa el 429 real) y `simulacion.py` (`ParametrosSimulacion`, `SimuladorMonitorias`, `ResultadoEscenario`).
- **Autoregistro:** botón «Crear cuenta de estudiante» en el login (acción pública `registrarse_estudiante`): crea su cuenta, notifica a Bienestar y entra directo a su panel sin token previo.
- **Configuración (los 6 roles):** módulo *Configuración* para teléfono, correo alterno y foto de perfil; la foto se sube desde archivo o se toma con la webcam (cámara centrada, JPEG 320×320).
- **Simulación de escenario (solo Admin):** módulo *Simulación* que corre una cola M/G/c por horas sobre la demanda real configurada (llegadas Poisson, servicio exponencial recortado 0,5–4 h, FCFS, desistimiento): histograma de esperas, KPIs y comparación de capacidad 1–4 monitores; motor determinista con semilla reproducible. Informe académico en [`docs/informe_n5.md`](docs/informe_n5.md).

## Estructura
```text
backend/app/modulos/  controladores por rol + reportes.py, perfil.py, registro.py, simulacion.py
backend/app/repositorio.py  patrón Repositorio sobre MySQL (lista blanca)
backend/app/errores.py  jerarquía de errores (mensaje + código HTTP)
backend/app/limites.py  limitador de peticiones (429) para acciones públicas
backend/app/simulacion.py  motor determinista de escenario M/G/c
backend/app/api.py  dispatcher POST /api
backend/app/rutas_extra.py  GET /health + GET /api/reportes/*
backend/app/esquema.sql  18 tablas PK/FK
backend/tests/  suite pytest (70 pruebas: unitarias + extremo a extremo)
frontend/js/modulos/  vistas SPA (incl. configuracion.js, simulacion.js, registro.js)
docs/  informe académico + diagramas PNG (ver Documentación)
```

## Instalación
1. Windows 10/11, Python 3.10+, MariaDB/MySQL corriendo.
2. Copie `backend/.env.example` a `backend/.env` y complete `DB_*`, `JWT_SECRETO` (32+ caracteres).
3. Doble clic `iniciar.bat` (crea `.venv`, instala `backend/requirements.txt`, crea BD, corre la suite automatizada y abre `http://127.0.0.1:8080`).
- Opciones: `iniciar.bat --reset` reconstruye la base con los datos de demo; `iniciar.bat --sin-tests` arranca sin la suite.
- Manual: `py -3 -m venv .venv` → `.\.venv\Scripts\python -m pip install -r backend\requirements.txt` → `pushd backend; ..\.venv\Scripts\python.exe preparar_bd.py; ..\.venv\Scripts\python.exe iniciar.py`.

## Base de datos
`preparar_bd.py` crea `gestor_monitorias` (`utf8mb4`) y reconcilia la migración declarativa de columnas de `usuarios` (teléfono, correo alterno, foto, sello de actualización). Al arrancar se aplica `esquema.sql` y, si `usuarios` está vacía, `datos_iniciales.py` carga la semilla de demostración (24 cuentas: 14 estudiantes, 5 profesores, 2 Bienestar, 2 Asesoría, 1 admin, 7 cursos, monitorías pasadas y programadas, notificaciones y calendario poblado). Rebuild completo: `preparar_bd.py --reset`. Modelo en [`docs/diagramas/mer.png`](docs/diagramas/mer.png) y [`docs/diagramas/modelo_relacional.png`](docs/diagramas/modelo_relacional.png).

Nota de convivencia: en esta máquina MariaDB también sirve a otros proyectos (por ejemplo `pos_factus`), y la contraseña de `root` puede cambiar desde herramientas externas — si la app reporta `Access denied for user 'root'`, restaure `root`/`0000` o (más estable) use en `backend/.env` el usuario dedicado de la app: `DB_USER=monitorias_app`, `DB_PASSWORD=monitorias2026`, con permisos totales sobre las bases `gestor%`. Re-crear ese usuario requiere pasos administrativos (`net stop MariaDB` + mysqld temporal con `--init-file` descrito en la sección 6 del informe).

## Ejecución y cuentas
Servidor solo `127.0.0.1:8080`. Credenciales **fijas** de demostración en `credenciales.txt` (raíz del proyecto, expuesto a propósito): la cuenta principal de cada rol usa `Rol#2026` — `estudiante camila.torres@ucc.edu.co / Estudiante#2026`, `monitor juan.perez@ucc.edu.co / Monitor#2026`, `profesor carlos.ramirez@ucc.edu.co / Profesor#2026`, `bienestar laura.gomez@ucc.edu.co / Bienestar#2026`, `asesoria andres.salazar@ucc.edu.co / Asesoria#2026`, `admin admin@ucc.edu.co / Admin#2026`. Nunca cambian con `--reset`; el resto de cuentas demo usa la fórmula `Prefijo#2026+Iniciales` (p. ej. `Est#2026SoR`), así el archivo es idéntico en cada corrida.

## Módulos y CRUD
- Estudiante: solicitudes (crear/listar), postulación, autoregistro desde el login.
- Monitor: tutorías (programar), informes (registrar).
- Profesor: listas de riesgo (crear/listar), validar informes.
- Bienestar: aprobar postulaciones e informes finales, riesgo global.
- Asesoría: asignar monitores, responder solicitudes.
- Reporte oficial: horas por monitor, monitorías por asignatura, solicitudes por estado + CSV.
- Transversales: panel por rol, calendario, notificaciones, auditoría, configuración de cuenta (telefono/correo/foto con webcam).

## Rutas
`POST /api` (SPA) + `GET /health` + `GET /api/reportes/horas-monitor|monitorias-asignatura|solicitudes-estado` (token `?token=` o `Authorization: Bearer`). Errores JSON `{ok:false}`. Las acciones públicas (`iniciar_sesion`, `registrarse_estudiante`, `renovar_sesion`) pasan por el limitador en memoria: máximo 10 intentos/min por IP+acción, respuesta `429` con auditoría «bloqueado».

## Pruebas
```bat
pushd backend
..\.venv\Scripts\python.exe -m pytest tests -q
```
72 pruebas: jerarquía de errores, validaciones, simulador (determinismo, comparación de capacidad, histograma), repositorio (lista blanca) + extremo a extremo con TestClient sobre la BD real (registro público → login → perfil → foto guardar/borrar → simulación → 429). Si MariaDB no está disponible, las pruebas con BD se omiten. `iniciar.bat` corre la suite antes de abrir el servidor.

Casos de uso en [`docs/diagramas/casos_uso.md`](docs/diagramas/casos_uso.md) y diagramas en `docs/diagramas/` (casos de uso, historias HU01–HU14, clases, MER, modelo relacional, 5 secuencias, arquitectura, actividad). Análisis N5: [`docs/informe_n5.md`](docs/informe_n5.md).

## Documentación

| Recurso | Archivo |
|---|---|
| Informe académico N5 (hipótesis, limitaciones, impacto) | [`docs/informe_n5.md`](docs/informe_n5.md) |
| Casos de uso (UC01–UC76) + funciones de la iteración 2 | [`docs/diagramas/casos_uso.md`](docs/diagramas/casos_uso.md) |
| Diagramas UML / MER / secuencias / arquitectura (PNG + PlantUML) | [`docs/diagramas/`](docs/diagramas/) |
| Credenciales fijas de demostración (1 por rol) | [`credenciales.txt`](credenciales.txt) |

## Contribución

Este es un proyecto académico abierto (licencia MIT). Los aportes de la comunidad y de
estudiantes de ingeniería son bienvenidos:

1. Haz un *fork* del repositorio y crea tu rama: `git checkout -b feature/mi-mejora`.
2. Ejecuta la suite: `pushd backend; ..\.venv\Scripts\python.exe -m pytest tests -q`.
3. Abre un *pull request* describiendo el cambio y la prueba que lo respalda.

## Licencia

[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-CAD400?style=flat-square)](LICENSE)

Distribuido bajo la **Licencia MIT** (código abierto): puedes usar, copiar, modificar y
distribuir el proyecto con fines académicos o comerciales, conservando el aviso de
licencia. Consulta el archivo [`LICENSE`](LICENSE) para el texto completo en español e inglés.

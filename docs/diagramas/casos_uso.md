# Diagramas — Gestor de Monitorías UCC

Todos los archivos viven en **esta misma carpeta** (`docs/diagramas/`): imagenes `.png` renderizadas y su fuente PlantUML `.puml` correspondiente.

| # | Diagrama | Imagen | Fuente |
|---|---|---|---|
| 1 | Casos de uso — 6 actores, 32 casos (UC01–UC76) | [`casos_uso.png`](casos_uso.png) | [`casos_uso.puml`](casos_uso.puml) |
| 2 | Historias de usuario HU01–HU14 | [`02_historias_usuario.jpg`](02_historias_usuario.jpg) | generador Python (solo imagen) |
| 3 | Clases UML — entidades + repositorio | [`clases.png`](clases.png) | [`clases.puml`](clases.puml) |
| 4 | MER — Entidad-Relación PK/FK | [`mer.png`](mer.png) | [`mer.puml`](mer.puml) |
| 5 | MR — Modelo relacional | [`modelo_relacional.png`](modelo_relacional.png) | [`modelo_relacional.puml`](modelo_relacional.puml) |
| 6 | Secuencia — inicio de sesión | [`secuencia_login.png`](secuencia_login.png) | [`secuencia_login.puml`](secuencia_login.puml) |
| 7 | Secuencia — solicitud UC10→UC52 | [`secuencia_solicitud.png`](secuencia_solicitud.png) | [`secuencia_solicitud.puml`](secuencia_solicitud.puml) |
| 8 | Secuencia — postulación UC12→UC41→UC71 | [`secuencia_postulacion.png`](secuencia_postulacion.png) | [`secuencia_postulacion.puml`](secuencia_postulacion.puml) |
| 9 | Secuencia — informe UC22→UC32→UC42 | [`secuencia_informe.png`](secuencia_informe.png) | [`secuencia_informe.puml`](secuencia_informe.puml) |
| 10 | Secuencia — riesgo UC30→UC51→UC21 | [`secuencia_riesgo.png`](secuencia_riesgo.png) | [`secuencia_riesgo.puml`](secuencia_riesgo.puml) |
| 11 | Arquitectura — componentes + despliegue | [`arquitectura.png`](arquitectura.png) | [`arquitectura.puml`](arquitectura.puml) |
| 12 | Actividad — ciclo de vida de la monitoría | [`actividad.png`](actividad.png) | [`actividad.puml`](actividad.puml) |

## Flujos por actor (resumen)

- **Estudiante:** solicitar monitoría → asesoría responde · postularse → bienestar decide → habilitación.
- **Monitor:** programar tutoría → registrar informe → validación → aprobación.
- **Profesor:** lista de riesgo → validar informes → reportes.
- **Bienestar:** decidir postulaciones → aprobación final → reportes.
- **Asesoría:** revisar listas → asignar monitor → responder solicitudes.
- **Admin:** crear usuarios/materias, activar/desactivar, restablecer claves, auditar, supervisar funciones.

## Iteración 2 — funciones nuevas (no presentes en el diagrama UC original)

Estas capacidades extendieron la iteración 1 y no re-renderizan el `.puml`; se acceden desde el menú propio de cada rol:

| Función | Rol | Módulo | Acción dispatcher |
|---|---|---|---|
| Autoregistro de cuenta de estudiante | público (sin token) | pantalla de login → "Crear cuenta de estudiante" | `registrarse_estudiante` |
| Configuración de cuenta (teléfono, correo alterno, foto con archivo o webcam) | los 6 roles | Configuración | `perfil_obtener`, `perfil_guardar`, `perfil_guardar_foto` |
| Laboratorio de simulación de demanda (cola M/G/c) | Admin | Simulación | `simulacion_ejecutar`, `simulacion_comparar` |

Análisis académico de la iteración 2 (hipotesis de mejora, limitaciones y generalización): ver [`../informe_n5.md`](../informe_n5.md).

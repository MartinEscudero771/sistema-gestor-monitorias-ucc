CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario VARCHAR(40) PRIMARY KEY,
    correo VARCHAR(160) NOT NULL UNIQUE,
    nombre VARCHAR(160) NOT NULL,
    hash_contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('estudiante', 'monitor', 'profesor', 'bienestar', 'asesoria', 'admin')),
    id_perfil VARCHAR(40) NOT NULL,
    telefono VARCHAR(30) NOT NULL DEFAULT '',
    correo_alternativo VARCHAR(160) NOT NULL DEFAULT '',
    foto_perfil MEDIUMTEXT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en VARCHAR(32) NOT NULL,
    actualizado_en VARCHAR(32) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS estudiantes (
    id_estudiante VARCHAR(40) PRIMARY KEY,
    nombre VARCHAR(160) NOT NULL,
    correo VARCHAR(160) NOT NULL,
    promedio DOUBLE NOT NULL CHECK (promedio >= 0 AND promedio <= 5),
    materias_reprobadas INT NOT NULL DEFAULT 0 CHECK (materias_reprobadas >= 0),
    programa VARCHAR(160) NOT NULL,
    semestre INT NOT NULL,
    horario_json LONGTEXT NOT NULL,
    creado_en VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS profesores (
    id_profesor VARCHAR(40) PRIMARY KEY,
    nombre VARCHAR(160) NOT NULL,
    correo VARCHAR(160) NOT NULL,
    departamento VARCHAR(160) NOT NULL,
    creado_en VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bienestar (
    id_bienestar VARCHAR(40) PRIMARY KEY,
    nombre VARCHAR(160) NOT NULL,
    cargo VARCHAR(160) NOT NULL,
    correo VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS docentes_asesoria (
    id_asesor VARCHAR(40) PRIMARY KEY,
    nombre VARCHAR(160) NOT NULL,
    correo VARCHAR(160) NOT NULL,
    cargo VARCHAR(160) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS monitores (
    id_monitor VARCHAR(40) PRIMARY KEY,
    id_estudiante VARCHAR(40) NOT NULL UNIQUE,
    asignatura VARCHAR(120) NOT NULL,
    max_horas_semanales INT NOT NULL DEFAULT 12,
    horario_json LONGTEXT NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('activo', 'inactivo')),
    validado_por VARCHAR(40),
    fecha_activacion VARCHAR(32),
    KEY idx_monitores_estado (estado),
    CONSTRAINT fk_monitor_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT fk_monitor_validador FOREIGN KEY (validado_por) REFERENCES bienestar(id_bienestar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS postulaciones_monitor (
    id_postulacion VARCHAR(40) PRIMARY KEY,
    id_estudiante VARCHAR(40) NOT NULL,
    asignatura VARCHAR(120) NOT NULL,
    horario_json LONGTEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobada', 'rechazada')),
    motivo_rechazo TEXT,
    revisado_por VARCHAR(40),
    fecha_creacion VARCHAR(32) NOT NULL,
    fecha_revision VARCHAR(32),
    KEY idx_postulaciones_estado (estado),
    CONSTRAINT fk_postulacion_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT fk_postulacion_revisor FOREIGN KEY (revisado_por) REFERENCES bienestar(id_bienestar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cursos (
    id_curso VARCHAR(40) PRIMARY KEY,
    id_profesor VARCHAR(40) NOT NULL,
    nombre VARCHAR(160) NOT NULL,
    codigo VARCHAR(40) NOT NULL UNIQUE,
    periodo VARCHAR(40) NOT NULL,
    CONSTRAINT fk_curso_profesor FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inscripciones (
    id_inscripcion VARCHAR(40) PRIMARY KEY,
    id_curso VARCHAR(40) NOT NULL,
    id_estudiante VARCHAR(40) NOT NULL,
    nota_final DOUBLE NOT NULL CHECK (nota_final >= 0 AND nota_final <= 5),
    UNIQUE KEY uq_inscripcion_curso_estudiante (id_curso, id_estudiante),
    CONSTRAINT fk_inscripcion_curso FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
    CONSTRAINT fk_inscripcion_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS listas_riesgo (
    id_lista VARCHAR(40) PRIMARY KEY,
    id_profesor VARCHAR(40) NOT NULL,
    id_curso VARCHAR(40) NOT NULL,
    asignatura VARCHAR(120) NOT NULL,
    fecha_creacion VARCHAR(32) NOT NULL,
    observaciones TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'enviada_asesoria' CHECK (estado IN ('enviada_asesoria', 'en_proceso', 'finalizada')),
    id_asesor VARCHAR(40),
    CONSTRAINT fk_lista_profesor FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    CONSTRAINT fk_lista_curso FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
    CONSTRAINT fk_lista_asesor FOREIGN KEY (id_asesor) REFERENCES docentes_asesoria(id_asesor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS riesgo_estudiantes (
    id_riesgo VARCHAR(40) PRIMARY KEY,
    id_lista VARCHAR(40) NOT NULL,
    id_estudiante VARCHAR(40) NOT NULL,
    motivo TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'asignado', 'atendido', 'cerrado')),
    fecha_creacion VARCHAR(32) NOT NULL,
    KEY idx_riesgo_lista (id_lista),
    CONSTRAINT fk_riesgo_lista FOREIGN KEY (id_lista) REFERENCES listas_riesgo(id_lista) ON DELETE CASCADE,
    CONSTRAINT fk_riesgo_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS asignaciones_riesgo (
    id_asignacion VARCHAR(40) PRIMARY KEY,
    id_riesgo VARCHAR(40) NOT NULL UNIQUE,
    id_monitor VARCHAR(40) NOT NULL,
    id_asesor VARCHAR(40) NOT NULL,
    observaciones TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'finalizada')),
    fecha_asignacion VARCHAR(32) NOT NULL,
    CONSTRAINT fk_asignacion_riesgo FOREIGN KEY (id_riesgo) REFERENCES riesgo_estudiantes(id_riesgo),
    CONSTRAINT fk_asignacion_monitor FOREIGN KEY (id_monitor) REFERENCES monitores(id_monitor),
    CONSTRAINT fk_asignacion_asesor FOREIGN KEY (id_asesor) REFERENCES docentes_asesoria(id_asesor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS monitorias (
    id_monitoria VARCHAR(40) PRIMARY KEY,
    id_monitor VARCHAR(40) NOT NULL,
    id_estudiante VARCHAR(40) NOT NULL,
    id_asignacion VARCHAR(40),
    id_profesor VARCHAR(40) NOT NULL,
    asignatura VARCHAR(120) NOT NULL,
    modalidad VARCHAR(20) NOT NULL CHECK (modalidad IN ('presencial', 'virtual')),
    aula_enlace VARCHAR(255) NOT NULL,
    fecha VARCHAR(10) NOT NULL,
    hora_inicio VARCHAR(5) NOT NULL,
    hora_fin VARCHAR(5) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'programada' CHECK (estado IN ('programada', 'realizada', 'cancelada')),
    creado_por VARCHAR(40) NOT NULL,
    fecha_creacion VARCHAR(32) NOT NULL,
    KEY idx_monitorias_monitor (id_monitor, fecha),
    KEY idx_monitorias_estudiante (id_estudiante, fecha),
    CONSTRAINT fk_monitoria_monitor FOREIGN KEY (id_monitor) REFERENCES monitores(id_monitor),
    CONSTRAINT fk_monitoria_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT fk_monitoria_asignacion FOREIGN KEY (id_asignacion) REFERENCES asignaciones_riesgo(id_asignacion),
    CONSTRAINT fk_monitoria_profesor FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS informes_horas (
    id_informe VARCHAR(40) PRIMARY KEY,
    id_monitor VARCHAR(40) NOT NULL,
    id_monitoria VARCHAR(40) NOT NULL UNIQUE,
    id_profesor VARCHAR(40) NOT NULL,
    id_estudiante VARCHAR(40) NOT NULL,
    fecha_sesion VARCHAR(10) NOT NULL,
    cantidad_horas DOUBLE NOT NULL CHECK (cantidad_horas > 0 AND cantidad_horas <= 4),
    actividades TEXT NOT NULL,
    estudiantes_atendidos TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente_profesor' CHECK (estado IN ('pendiente_profesor', 'pendiente_bienestar', 'aprobado', 'rechazado')),
    firma_profesor VARCHAR(160),
    id_aprobador_bienestar VARCHAR(40),
    observacion_revision TEXT,
    fecha_creacion VARCHAR(32) NOT NULL,
    fecha_actualizacion VARCHAR(32),
    KEY idx_informes_profesor (id_profesor, estado),
    KEY idx_informes_monitor (id_monitor, fecha_sesion),
    CONSTRAINT fk_informe_monitor FOREIGN KEY (id_monitor) REFERENCES monitores(id_monitor),
    CONSTRAINT fk_informe_monitoria FOREIGN KEY (id_monitoria) REFERENCES monitorias(id_monitoria),
    CONSTRAINT fk_informe_profesor FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
    CONSTRAINT fk_informe_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT fk_informe_aprobador FOREIGN KEY (id_aprobador_bienestar) REFERENCES bienestar(id_bienestar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS solicitudes_monitoria (
    id_solicitud VARCHAR(40) PRIMARY KEY,
    id_estudiante VARCHAR(40) NOT NULL,
    asignatura VARCHAR(120) NOT NULL,
    tema VARCHAR(300) NOT NULL,
    fecha_preferida VARCHAR(10) NOT NULL,
    hora_preferida VARCHAR(5) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aceptada', 'rechazada')),
    respuesta TEXT,
    id_asesor VARCHAR(40),
    fecha_creacion VARCHAR(32) NOT NULL,
    fecha_respuesta VARCHAR(32),
    CONSTRAINT fk_solicitud_estudiante FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
    CONSTRAINT fk_solicitud_asesor FOREIGN KEY (id_asesor) REFERENCES docentes_asesoria(id_asesor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notificaciones (
    id_notificacion VARCHAR(40) PRIMARY KEY,
    id_usuario VARCHAR(40) NOT NULL,
    titulo VARCHAR(160) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'informacion' CHECK (tipo IN ('informacion', 'exito', 'alerta')),
    leida TINYINT(1) NOT NULL DEFAULT 0 CHECK (leida IN (0, 1)),
    fecha_creacion VARCHAR(32) NOT NULL,
    KEY idx_notificaciones_usuario (id_usuario, leida),
    CONSTRAINT fk_notificacion_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sesiones (
    id_sesion VARCHAR(40) PRIMARY KEY,
    id_usuario VARCHAR(40) NOT NULL,
    hash_refresh VARCHAR(128) NOT NULL UNIQUE,
    fecha_creacion VARCHAR(32) NOT NULL,
    fecha_expiracion VARCHAR(32) NOT NULL,
    ultima_actividad VARCHAR(32) NOT NULL,
    ip_hash VARCHAR(64) NOT NULL,
    agente_hash VARCHAR(64) NOT NULL,
    revocada TINYINT(1) NOT NULL DEFAULT 0 CHECK (revocada IN (0, 1)),
    KEY idx_sesiones_usuario (id_usuario, revocada),
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_usuario VARCHAR(40),
    id_usuario_objetivo VARCHAR(40),
    accion VARCHAR(80) NOT NULL,
    resultado VARCHAR(20) NOT NULL,
    id_solicitud VARCHAR(80),
    direccion_ip VARCHAR(64),
    agente VARCHAR(255),
    detalle LONGTEXT,
    fecha_creacion VARCHAR(32) NOT NULL,
    KEY idx_auditoria_fecha (fecha_creacion),
    KEY idx_auditoria_usuario (id_usuario, fecha_creacion),
    KEY idx_auditoria_accion (accion, fecha_creacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

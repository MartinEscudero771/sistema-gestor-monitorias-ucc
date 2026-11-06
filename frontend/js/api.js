window.api_ucc = (function () {
    const tiempo_maximo = 20000;
    let token_actual = "";
    let id_usuario_objetivo = "";
    let al_cambiar_no_leidas = function () {};
    const ACCIONES_SIN_OBJETIVO = new Set([
        "iniciar_sesion",
        "renovar_sesion",
        "sesion_consultar",
        "sesion_cerrar",
        "cambiar_contrasena",
        "notificaciones_listar",
        "notificaciones_marcar_leida",
        "notificaciones_marcar_todas",
        "auditoria_listar",
        "admin_usuarios",
        "admin_contexto",
        "admin_crear_usuario",
        "admin_estado_usuario",
        "admin_reset_contrasena",
        "admin_cursos",
        "admin_crear_curso",
        "admin_estudiantes",
        "perfil_obtener",
        "perfil_guardar",
        "perfil_guardar_foto",
        "simulacion_ejecutar",
        "simulacion_comparar"
    ]);

    function guardar_token(token) {
        token_actual = token || "";
    }

    function borrar_token() {
        token_actual = "";
    }

    function establecer_usuario_objetivo(id_usuario) {
        id_usuario_objetivo = String(id_usuario || "").trim();
    }

    function obtener_usuario_objetivo() {
        return id_usuario_objetivo;
    }

    function limpiar_usuario_objetivo() {
        id_usuario_objetivo = "";
    }

    function mensaje_error(cuerpo) {
        if (cuerpo && typeof cuerpo.mensaje === "string") {
            return cuerpo.mensaje;
        }
        return "No fue posible completar la solicitud.";
    }

    async function enviar_accion(accion, datos, opciones) {
        const datos_solicitud = Object.assign({}, datos || {});
        if (
            id_usuario_objetivo &&
            !ACCIONES_SIN_OBJETIVO.has(accion) &&
            !datos_solicitud.id_usuario_objetivo
        ) {
            datos_solicitud.id_usuario_objetivo = id_usuario_objetivo;
        }
        const cuerpo_envio = {
            accion: accion,
            datos: datos_solicitud
        };
        if (token_actual) {
            cuerpo_envio.token = token_actual;
        }

        const controlador = new AbortController();
        const temporizador = window.setTimeout(function () {
            controlador.abort();
        }, tiempo_maximo);
        let respuesta;
        try {
            respuesta = await fetch("/api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cuerpo_envio),
                credentials: "same-origin",
                cache: "no-store",
                signal: controlador.signal
            });
        } catch (error) {
            const error_conexion = new Error(
                error && error.name === "AbortError"
                    ? "El servidor tardó demasiado en responder. Intente nuevamente."
                    : "No fue posible conectar con el servidor."
            );
            error_conexion.codigo = 0;
            throw error_conexion;
        } finally {
            window.clearTimeout(temporizador);
        }

        let cuerpo;
        try {
            cuerpo = await respuesta.json();
        } catch (error) {
            const error_formato = new Error(
                "El servidor devolvió una respuesta que no se pudo interpretar."
            );
            error_formato.codigo = respuesta.status;
            throw error_formato;
        }

        if (cuerpo && cuerpo.seguridad && typeof cuerpo.seguridad.token === "string") {
            guardar_token(cuerpo.seguridad.token);
        }
        if (cuerpo && cuerpo.datos) {
            const no_leidas =
                typeof cuerpo.datos.no_leidas_admin === "number"
                    ? cuerpo.datos.no_leidas_admin
                    : cuerpo.datos.no_leidas;
            if (typeof no_leidas === "number") {
                al_cambiar_no_leidas(no_leidas);
            }
        }

        if (!respuesta.ok || !cuerpo || cuerpo.ok !== true) {
            const error_api = new Error(mensaje_error(cuerpo));
            error_api.codigo =
                cuerpo && typeof cuerpo.codigo === "number"
                    ? cuerpo.codigo
                    : respuesta.status;
            error_api.accion = accion;
            throw error_api;
        }

        if (cuerpo.datos && cuerpo.datos.cerrar_sesion) {
            borrar_token();
        }
        return cuerpo.datos || {};
    }

    async function renovar_sesion() {
        try {
            return await enviar_accion("renovar_sesion", {}, { reintentado: true });
        } catch (error) {
            borrar_token();
            throw error;
        }
    }

    async function llamar(accion, datos, opciones) {
        const configuracion = Object.assign({}, opciones || {});
        const acciones_publicas = [
            "iniciar_sesion",
            "renovar_sesion",
            "registrarse_estudiante"
        ];
        try {
            return await enviar_accion(accion, datos, configuracion);
        } catch (error) {
            if (
                error &&
                error.codigo === 401 &&
                acciones_publicas.indexOf(accion) === -1 &&
                !configuracion.reintentado
            ) {
                try {
                    const sesion_renovada = await renovar_sesion();
                    const resultado = await llamar(accion, datos, { reintentado: true });
                    return Object.assign({}, resultado, {
                        _sesion_renovada: sesion_renovada
                    });
                } catch (error_renovacion) {
                    borrar_token();
                    window.dispatchEvent(
                        new CustomEvent("ucc_sesion_expirada", {
                            detail: { mensaje: error_renovacion.message }
                        })
                    );
                    throw error_renovacion;
                }
            }
            throw error;
        }
    }

    function configurar_callback_no_leidas(funcion_callback) {
        al_cambiar_no_leidas =
            typeof funcion_callback === "function"
                ? funcion_callback
                : function () {};
    }

    return {
        llamar: llamar,
        renovar_sesion: renovar_sesion,
        guardar_token: guardar_token,
        borrar_token: borrar_token,
        establecer_usuario_objetivo: establecer_usuario_objetivo,
        obtener_usuario_objetivo: obtener_usuario_objetivo,
        limpiar_usuario_objetivo: limpiar_usuario_objetivo,
        configurar_callback_no_leidas: configurar_callback_no_leidas
    };
})();

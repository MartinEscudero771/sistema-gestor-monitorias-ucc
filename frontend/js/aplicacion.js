window.app_ucc = (function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    const pantalla_carga = document.getElementById("pantalla_carga");
    const pantalla_login = document.getElementById("pantalla_login");
    const aplicacion = document.getElementById("aplicacion");
    const formulario_login = document.getElementById("formulario_login");
    const correo_login = document.getElementById("correo_login");
    const contrasena_login = document.getElementById("contrasena_login");
    const boton_login = document.getElementById("boton_login");
    const boton_ver_contrasena = document.getElementById(
        "boton_ver_contrasena"
    );
    const alerta_login = document.getElementById("alerta_login");
    const navegacion_modulos = document.getElementById("navegacion_modulos");
    const nombre_usuario = document.getElementById("nombre_usuario");
    const rol_usuario = document.getElementById("rol_usuario");
    const avatar_usuario = document.getElementById("avatar_usuario");
    const cabecera_rol = document.getElementById("cabecera_rol");
    const titulo_modulo = document.getElementById("titulo_modulo");
    const vista_modulo = document.getElementById("vista_modulo");
    const boton_cerrar_sesion = document.getElementById("boton_cerrar_sesion");
    const boton_cambiar_contrasena = document.getElementById(
        "boton_cambiar_contrasena"
    );
    const modal_contrasena = document.getElementById(
        "modal_cambiar_contrasena"
    );
    const formulario_contrasena = document.getElementById(
        "formulario_cambiar_contrasena"
    );
    const alerta_contrasena = document.getElementById(
        "alerta_cambiar_contrasena"
    );
    const contrasena_actual = document.getElementById("contrasena_actual");
    const contrasena_nueva = document.getElementById("contrasena_nueva");
    const confirmacion_contrasena = document.getElementById(
        "confirmacion_contrasena"
    );
    const boton_guardar_contrasena = document.getElementById(
        "boton_guardar_contrasena"
    );

    let usuario_actual = null;
    let modulos_actuales = [];
    let contexto_actual = null;
    let contexto_admin = null;
    let modulo_objetivo_actual = null;
    let generacion_vista = 0;
    let arrancado = false;
    let ingresando = false;
    let cambiando_contrasena = false;
    let cerrando_sesion = false;

    function crear_contexto() {
        generacion_vista += 1;
        const generacion = generacion_vista;
        return {
            vigente: function () {
                return generacion === generacion_vista && !!usuario_actual;
            }
        };
    }

    function invalidar_contexto() {
        generacion_vista += 1;
        contexto_actual = null;
    }

    function limpiar_contexto_admin() {
        contexto_admin = null;
        modulo_objetivo_actual = null;
        api.limpiar_usuario_objetivo();
    }

    function obtener_usuario() {
        return usuario_actual;
    }

    function actualizar_avatar(foto, nombre_fallback) {
        if (!avatar_usuario) {
            return;
        }
        const nombre =
            nombre_fallback ||
            (usuario_actual ? usuario_actual.nombre : "") ||
            "U";
        if (foto) {
            utilidades.vaciar(avatar_usuario);
            avatar_usuario.classList.add("avatar_con_foto");
            const imagen = document.createElement("img");
            imagen.src = foto;
            imagen.alt = "Foto de perfil de " + nombre;
            avatar_usuario.append(imagen);
        } else {
            avatar_usuario.classList.remove("avatar_con_foto");
            avatar_usuario.textContent = utilidades.iniciales(nombre);
        }
    }

    function actualizar_identidad(usuario) {
        if (!usuario || !usuario_actual) {
            return;
        }
        if (usuario.nombre && usuario.nombre !== usuario_actual.nombre) {
            usuario_actual.nombre = usuario.nombre;
            if (nombre_usuario) {
                nombre_usuario.textContent = usuario.nombre;
            }
        }
        if (usuario.rol_texto) {
            usuario_actual.rol_texto = usuario.rol_texto;
            if (rol_usuario) {
                rol_usuario.textContent = usuario.rol_texto;
            }
            if (cabecera_rol) {
                cabecera_rol.textContent = usuario.rol_texto;
            }
        }
        if (usuario.foto !== undefined) {
            usuario_actual.foto = usuario.foto;
            actualizar_avatar(usuario.foto);
        }
    }

    function mostrar_alerta_login(mensaje, tipo) {
        if (!alerta_login) {
            return;
        }
        const nivel =
            tipo === "exito"
                ? "success"
                : tipo === "info"
                  ? "info"
                  : tipo === "advertencia"
                    ? "warning"
                    : "danger";
        alerta_login.className = "alert alert-" + nivel;
        alerta_login.textContent = mensaje;
        alerta_login.classList.remove("d-none");
    }

    function ocultar_alerta_login() {
        if (!alerta_login) {
            return;
        }
        alerta_login.textContent = "";
        alerta_login.classList.add("d-none");
    }

    function mostrar_login(mensaje, tipo) {
        if (pantalla_carga) {
            pantalla_carga.classList.add("d-none");
        }
        if (aplicacion) {
            aplicacion.classList.add("d-none");
        }
        if (pantalla_login) {
            pantalla_login.classList.remove("d-none");
        }
        document.title = "Gestor de Monitorías Académicas UCC";
        if (mensaje) {
            mostrar_alerta_login(mensaje, tipo);
        } else {
            ocultar_alerta_login();
        }
    }

    function cerrar_offcanvas(id) {
        if (
            typeof bootstrap === "undefined" ||
            !bootstrap.Offcanvas
        ) {
            return;
        }
        const panel = document.getElementById(id);
        if (!panel) {
            return;
        }
        const instancia = bootstrap.Offcanvas.getInstance(panel);
        if (instancia) {
            instancia.hide();
        }
    }

    function cerrar_menu_lateral() {
        cerrar_offcanvas("barra_lateral");
    }

    function cerrar_paneles_flotantes() {
        cerrar_offcanvas("panel_notificaciones");
        cerrar_offcanvas("barra_lateral");
        if (modal_contrasena && bootstrap.Modal) {
            const instancia_modal = bootstrap.Modal.getInstance(
                modal_contrasena
            );
            if (instancia_modal) {
                instancia_modal.hide();
            }
        }
    }

    function construir_menu() {
        if (!navegacion_modulos) {
            return;
        }
        utilidades.vaciar(navegacion_modulos);
        modulos_actuales.forEach(function (modulo) {
            const boton = utilidades.crear("button", "boton_modulo");
            boton.type = "button";
            boton.dataset.clave = modulo.clave;
            boton.append(
                utilidades.icono(modulo.icono || "bi-circle"),
                utilidades.crear("span", "", modulo.titulo)
            );
            boton.addEventListener("click", function () {
                abrir_modulo(modulo.clave);
            });
            navegacion_modulos.append(boton);
        });
    }

    function marcar_modulo_activo(clave) {
        if (!navegacion_modulos) {
            return;
        }
        const botones = navegacion_modulos.querySelectorAll(".boton_modulo");
        botones.forEach(function (boton) {
            const activo = boton.dataset.clave === clave;
            boton.classList.toggle("activo", activo);
            if (activo) {
                boton.setAttribute("aria-current", "page");
            } else {
                boton.removeAttribute("aria-current");
            }
        });
    }

    function actualizar_encabezado(modulo) {
        if (titulo_modulo) {
            titulo_modulo.textContent = modulo.titulo;
        }
        if (cabecera_rol && usuario_actual) {
            cabecera_rol.textContent = usuario_actual.rol_texto;
        }
        document.title =
            modulo.titulo + " · Gestor de Monitorías Académicas UCC";
        marcar_modulo_activo(modulo.clave);
    }

    function obtener_vista(modulo, rol) {
        const rol_efectivo = rol || (usuario_actual ? usuario_actual.rol : "");
        if (modulo.clave === "validar_horas") {
            if (rol_efectivo === "bienestar") {
                return window.vistas_ucc.validar_horas_bienestar;
            }
            return window.vistas_ucc.validar_horas_profesor;
        }
        return window.vistas_ucc[modulo.clave];
    }

    async function abrir_modulo(clave) {
        if (!usuario_actual) {
            return;
        }
        if (contexto_admin && clave !== "supervision") {
            limpiar_contexto_admin();
        }
        const modulo = modulos_actuales.find(function (item) {
            return item.clave === clave;
        });
        if (!modulo) {
            return;
        }

        actualizar_encabezado(modulo);
        cerrar_menu_lateral();
        contexto_actual = crear_contexto();
        const contexto = contexto_actual;
        window.scrollTo({ top: 0, behavior: "smooth" });

        const vista = obtener_vista(modulo);
        if (typeof vista !== "function") {
            utilidades.mostrar_error(
                vista_modulo,
                "El módulo solicitado no está disponible.",
                function () {
                    abrir_modulo(clave);
                }
            );
            return;
        }

        utilidades.mostrar_carga(vista_modulo, "Cargando el módulo...");
        try {
            await vista(vista_modulo, contexto);
        } catch (error) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.mostrar_error(vista_modulo, error.message, function () {
                abrir_modulo(clave);
            });
        }
    }

    function mostrar_panel_inicial(panel) {
        const modulo_inicio = modulos_actuales.find(function (modulo) {
            return modulo.clave === "inicio";
        });

        if (!modulo_inicio) {
            if (titulo_modulo) {
                titulo_modulo.textContent = "Inicio";
            }
            utilidades.mostrar_error(
                vista_modulo,
                "No hay módulos disponibles para este usuario."
            );
            return;
        }

        actualizar_encabezado(modulo_inicio);
        contexto_actual = crear_contexto();
        if (
            typeof window.vistas_ucc.inicio === "function" &&
            typeof window.vistas_ucc.inicio.dibujar_panel === "function"
        ) {
            window.vistas_ucc.inicio.dibujar_panel(vista_modulo, panel);
        } else {
            abrir_modulo(modulo_inicio.clave);
        }
    }

    function crear_bandeja_supervision() {
        const caja = utilidades.crear("section", "bandeja_supervision");
        caja.setAttribute("role", "status");
        const usuario = contexto_admin ? contexto_admin.usuario_objetivo : null;
        const texto = utilidades.crear("div", "bandeja_supervision_texto");
        texto.append(
            utilidades.crear(
                "p",
                "bandeja_supervision_etiqueta",
                "Supervisión administrativa"
            ),
            utilidades.crear(
                "p",
                "",
                usuario
                    ? "Está operando el sistema como " +
                          usuario.nombre +
                          " (" +
                          usuario.rol_texto +
                          "). Cada acción queda registrada en auditoría."
                    : "Supervisión administrativa activa."
            )
        );
        const acciones = utilidades.crear(
            "div",
            "bandeja_supervision_acciones"
        );
        acciones.append(
            utilidades.boton(
                "Volver a supervisión",
                "bi-arrow-left",
                "boton_claro boton_pequeno",
                volver_a_supervision
            ),
            utilidades.boton(
                "Finalizar supervisión",
                "bi-x-lg",
                "boton_peligro boton_pequeno",
                salir_supervision
            )
        );
        caja.append(texto, acciones);
        return caja;
    }

    function volver_a_supervision() {
        if (!contexto_admin) {
            return;
        }
        api.limpiar_usuario_objetivo();
        modulo_objetivo_actual = null;
        abrir_modulo("supervision");
    }

    function salir_supervision() {
        limpiar_contexto_admin();
        abrir_modulo("supervision");
    }

    async function supervisar_usuario(id_usuario) {
        if (!usuario_actual || usuario_actual.rol !== "admin") {
            return;
        }
        const datos = await api.llamar("admin_contexto", {
            id_usuario: id_usuario
        });
        if (!datos.usuario_objetivo || !datos.usuario_objetivo.id_usuario) {
            throw new Error("No fue posible abrir el contexto del usuario.");
        }
        contexto_admin = datos;
        modulo_objetivo_actual = null;
        api.establecer_usuario_objetivo(datos.usuario_objetivo.id_usuario);
        utilidades.toast(
            "Supervisando a " + datos.usuario_objetivo.nombre + ".",
            "info"
        );
        abrir_modulo("supervision");
    }

    async function abrir_modulo_objetivo(clave) {
        if (!contexto_admin || !usuario_actual) {
            return;
        }
        const modulo = (contexto_admin.modulos || []).find(function (item) {
            return item.clave === clave;
        });
        if (!modulo) {
            return;
        }
        api.establecer_usuario_objetivo(
            contexto_admin.usuario_objetivo.id_usuario
        );
        modulo_objetivo_actual = modulo;
        actualizar_encabezado(modulo);
        marcar_modulo_activo("supervision");
        if (cabecera_rol) {
            cabecera_rol.textContent =
                "Supervisión: " + contexto_admin.usuario_objetivo.nombre;
        }
        cerrar_menu_lateral();
        contexto_actual = crear_contexto();
        const contexto = contexto_actual;
        window.scrollTo({ top: 0, behavior: "smooth" });

        if (clave === "inicio") {
            utilidades.vaciar(vista_modulo);
            if (
                typeof window.vistas_ucc.inicio === "function" &&
                typeof window.vistas_ucc.inicio.dibujar_panel === "function"
            ) {
                window.vistas_ucc.inicio.dibujar_panel(
                    vista_modulo,
                    contexto_admin.panel
                );
            }
            if (contexto.vigente() && modulo_objetivo_actual === modulo) {
                vista_modulo.prepend(crear_bandeja_supervision());
            }
            return;
        }

        const vista = obtener_vista(
            modulo,
            contexto_admin.usuario_objetivo.rol
        );
        if (typeof vista !== "function") {
            utilidades.mostrar_error(
                vista_modulo,
                "El módulo solicitado no está disponible para este usuario.",
                function () {
                    abrir_modulo_objetivo(clave);
                }
            );
            return;
        }

        utilidades.mostrar_carga(vista_modulo, "Cargando el módulo...");
        try {
            await vista(vista_modulo, contexto);
            if (contexto.vigente() && modulo_objetivo_actual === modulo) {
                vista_modulo.prepend(crear_bandeja_supervision());
            }
        } catch (error) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.mostrar_error(vista_modulo, error.message, function () {
                abrir_modulo_objetivo(clave);
            });
            vista_modulo.prepend(crear_bandeja_supervision());
        }
    }

    function aplicar_sesion(datos) {
        usuario_actual = datos.usuario;
        modulos_actuales = Array.isArray(datos.modulos) ? datos.modulos : [];
        limpiar_contexto_admin();
        if (datos.token) {
            api.guardar_token(datos.token);
        }

        if (pantalla_carga) {
            pantalla_carga.classList.add("d-none");
        }
        if (pantalla_login) {
            pantalla_login.classList.add("d-none");
        }
        if (aplicacion) {
            aplicacion.classList.remove("d-none");
        }
        ocultar_alerta_login();

        if (nombre_usuario) {
            nombre_usuario.textContent = usuario_actual.nombre;
        }
        if (rol_usuario) {
            rol_usuario.textContent = usuario_actual.rol_texto;
        }
        actualizar_avatar(usuario_actual.foto, usuario_actual.nombre);
        if (cabecera_rol) {
            cabecera_rol.textContent = usuario_actual.rol_texto;
        }

        construir_menu();

        if (window.notificaciones_ucc) {
            window.notificaciones_ucc.iniciar();
            window.notificaciones_ucc.reiniciar();
            window.notificaciones_ucc.actualizar_contador(
                Number(datos.no_leidas) || 0
            );
        }

        mostrar_panel_inicial(datos.panel);

        if (formulario_login) {
            formulario_login.classList.remove("was-validated");
            formulario_login.reset();
        }
    }

    function adoptar_sesion(datos, mensaje_bienvenida) {
        aplicar_sesion(datos);
        if (mensaje_bienvenida) {
            utilidades.toast(mensaje_bienvenida, "exito");
        }
    }

    function finalizar_sesion(mensaje, tipo) {
        invalidar_contexto();
        limpiar_contexto_admin();
        usuario_actual = null;
        modulos_actuales = [];
        api.borrar_token();
        cerrar_paneles_flotantes();

        if (window.notificaciones_ucc) {
            window.notificaciones_ucc.reiniciar();
        }

        if (nombre_usuario) {
            nombre_usuario.textContent = "Usuario";
        }
        if (rol_usuario) {
            rol_usuario.textContent = "Rol";
        }
        actualizar_avatar("", "Usuario");
        if (cabecera_rol) {
            cabecera_rol.textContent = "Panel académico";
        }
        if (titulo_modulo) {
            titulo_modulo.textContent = "Inicio";
        }
        if (navegacion_modulos) {
            utilidades.vaciar(navegacion_modulos);
        }
        if (vista_modulo) {
            utilidades.vaciar(vista_modulo);
        }
        if (formulario_login) {
            formulario_login.classList.remove("was-validated");
            formulario_login.reset();
        }
        if (formulario_contrasena) {
            formulario_contrasena.classList.remove("was-validated");
            formulario_contrasena.reset();
        }
        if (alerta_contrasena) {
            alerta_contrasena.textContent = "";
            alerta_contrasena.classList.add("d-none");
        }
        if (contrasena_login) {
            contrasena_login.type = "password";
        }
        if (boton_ver_contrasena) {
            utilidades.reemplazar_icono(boton_ver_contrasena, "bi-eye");
            boton_ver_contrasena.setAttribute(
                "aria-label",
                "Mostrar contraseña"
            );
            boton_ver_contrasena.title = "Mostrar contraseña";
        }
        const zona_toasts = document.getElementById("zona_toasts");
        if (zona_toasts) {
            utilidades.vaciar(zona_toasts);
        }

        mostrar_login(mensaje, tipo);
        window.scrollTo({ top: 0, behavior: "auto" });
    }

    async function manejar_login(evento) {
        evento.preventDefault();
        if (ingresando) {
            return;
        }
        ocultar_alerta_login();

        if (!formulario_login.checkValidity()) {
            formulario_login.classList.add("was-validated");
            formulario_login.reportValidity();
            return;
        }

        const correo = correo_login.value.trim();
        correo_login.value = correo;
        const contrasena = contrasena_login.value;

        ingresando = true;
        utilidades.ocupar_boton(boton_login, true, "Ingresando...");
        try {
            const datos = await api.llamar("iniciar_sesion", {
                correo: correo,
                contrasena: contrasena
            });
            aplicar_sesion(datos);
        } catch (error) {
            mostrar_alerta_login(error.message, "error");
            contrasena_login.value = "";
            contrasena_login.focus();
        } finally {
            ingresando = false;
            utilidades.ocupar_boton(boton_login, false);
        }
    }

    function alternar_contrasena_login() {
        if (!contrasena_login || !boton_ver_contrasena) {
            return;
        }
        const visible = contrasena_login.type === "text";
        contrasena_login.type = visible ? "password" : "text";
        utilidades.reemplazar_icono(
            boton_ver_contrasena,
            visible ? "bi-eye" : "bi-eye-slash"
        );
        const etiqueta = visible ? "Mostrar contraseña" : "Ocultar contraseña";
        boton_ver_contrasena.setAttribute("aria-label", etiqueta);
        boton_ver_contrasena.title = etiqueta;
    }

    function abrir_modal_contrasena() {
        if (!usuario_actual || !modal_contrasena) {
            return;
        }
        if (formulario_contrasena) {
            formulario_contrasena.reset();
            formulario_contrasena.classList.remove("was-validated");
        }
        if (alerta_contrasena) {
            alerta_contrasena.textContent = "";
            alerta_contrasena.classList.add("d-none");
        }
        if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            bootstrap.Modal.getOrCreateInstance(modal_contrasena).show();
        }
    }

    function mostrar_error_contrasena(mensaje) {
        if (!alerta_contrasena) {
            return;
        }
        alerta_contrasena.textContent = mensaje;
        alerta_contrasena.className = "alert alert-danger";
        alerta_contrasena.classList.remove("d-none");
    }

    async function manejar_cambio_contrasena(evento) {
        evento.preventDefault();
        if (cambiando_contrasena) {
            return;
        }
        if (!formulario_contrasena.checkValidity()) {
            formulario_contrasena.classList.add("was-validated");
            formulario_contrasena.reportValidity();
            return;
        }
        if (alerta_contrasena) {
            alerta_contrasena.textContent = "";
            alerta_contrasena.classList.add("d-none");
        }

        const actual = contrasena_actual.value;
        const nueva = contrasena_nueva.value;
        const confirmacion = confirmacion_contrasena.value;

        if (nueva !== confirmacion) {
            mostrar_error_contrasena(
                "La confirmación de la contraseña no coincide."
            );
            confirmacion_contrasena.focus();
            return;
        }
        if (nueva === actual) {
            mostrar_error_contrasena(
                "La contraseña nueva debe ser diferente a la actual."
            );
            contrasena_nueva.focus();
            return;
        }

        cambiando_contrasena = true;
        utilidades.ocupar_boton(
            boton_guardar_contrasena,
            true,
            "Actualizando..."
        );
        try {
            const datos = await api.llamar("cambiar_contrasena", {
                contrasena_actual: actual,
                contrasena_nueva: nueva,
                confirmacion_contrasena: confirmacion
            });
            if (!usuario_actual) {
                return;
            }
            if (formulario_contrasena) {
                formulario_contrasena.reset();
            }
            finalizar_sesion(
                datos.mensaje ||
                    "Contraseña actualizada. Inicie sesión nuevamente.",
                "exito"
            );
        } catch (error) {
            if (!usuario_actual) {
                return;
            }
            mostrar_error_contrasena(error.message);
        } finally {
            cambiando_contrasena = false;
            utilidades.ocupar_boton(boton_guardar_contrasena, false);
        }
    }

    async function cerrar_sesion_servidor() {
        if (cerrando_sesion || !usuario_actual) {
            return;
        }
        cerrando_sesion = true;
        utilidades.ocupar_boton(
            boton_cerrar_sesion,
            true,
            "Cerrando..."
        );
        let mensaje = "La sesión se cerró correctamente.";
        let tipo = "exito";
        try {
            const datos = await api.llamar("sesion_cerrar");
            mensaje = datos.mensaje || mensaje;
        } catch (error) {
            if (error.codigo === 401) {
                return;
            }
            mensaje =
                "Se cerró la sesión en este dispositivo. El servidor no confirmó la operación.";
            tipo = "advertencia";
        } finally {
            cerrando_sesion = false;
            utilidades.ocupar_boton(boton_cerrar_sesion, false);
            if (usuario_actual) {
                finalizar_sesion(mensaje, tipo);
            }
        }
    }

    function manejar_sesion_expirada(evento) {
        if (!usuario_actual) {
            return;
        }
        const mensaje =
            evento && evento.detail && evento.detail.mensaje
                ? evento.detail.mensaje
                : "Su sesión expiró. Ingrese nuevamente.";
        finalizar_sesion(mensaje, "error");
    }

    function configurar_eventos() {
        if (formulario_login) {
            formulario_login.addEventListener("submit", manejar_login);
        }
        if (boton_ver_contrasena) {
            boton_ver_contrasena.addEventListener(
                "click",
                alternar_contrasena_login
            );
        }
        if (boton_cerrar_sesion) {
            boton_cerrar_sesion.addEventListener(
                "click",
                cerrar_sesion_servidor
            );
        }
        if (boton_cambiar_contrasena) {
            boton_cambiar_contrasena.addEventListener(
                "click",
                abrir_modal_contrasena
            );
        }
        if (formulario_contrasena) {
            formulario_contrasena.addEventListener(
                "submit",
                manejar_cambio_contrasena
            );
        }
        if (modal_contrasena) {
            modal_contrasena.addEventListener("hidden.bs.modal", function () {
                if (!cambiando_contrasena && formulario_contrasena) {
                    formulario_contrasena.reset();
                    formulario_contrasena.classList.remove("was-validated");
                }
                if (!cambiando_contrasena && alerta_contrasena) {
                    alerta_contrasena.textContent = "";
                    alerta_contrasena.classList.add("d-none");
                }
            });
        }
        window.addEventListener(
            "ucc_sesion_expirada",
            manejar_sesion_expirada
        );
    }

    async function iniciar() {
        if (arrancado) {
            return;
        }
        arrancado = true;
        configurar_eventos();

        api.configurar_callback_no_leidas(function (cantidad) {
            if (
                usuario_actual &&
                !api.obtener_usuario_objetivo() &&
                window.notificaciones_ucc
            ) {
                window.notificaciones_ucc.actualizar_contador(cantidad);
            }
        });

        try {
            const datos = await api.renovar_sesion();
            aplicar_sesion(datos);
        } catch (error) {
            if (error.codigo === 401) {
                mostrar_login();
            } else {
                mostrar_login(
                    "No fue posible verificar su sesión. Intente ingresar nuevamente.",
                    "error"
                );
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }

    return {
        obtener_usuario: obtener_usuario,
        abrir_modulo: abrir_modulo,
        supervisar_usuario: supervisar_usuario,
        abrir_modulo_objetivo: abrir_modulo_objetivo,
        adoptar_sesion: adoptar_sesion,
        actualizar_identidad: actualizar_identidad,
        actualizar_avatar: actualizar_avatar,
        obtener_contexto_admin: function () {
            return contexto_admin;
        },
        volver_a_supervision: volver_a_supervision,
        salir_supervision: salir_supervision
    };
})();

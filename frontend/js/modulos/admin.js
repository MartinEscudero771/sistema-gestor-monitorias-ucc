window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    function es_supervisable(usuario) {
        const actual = window.app_ucc.obtener_usuario();
        return Boolean(
            usuario.activo &&
                usuario.id_usuario !== (actual && actual.id_usuario)
        );
    }

    function formatear_fecha_hora(valor) {
        if (!valor) {
            return "Sin registro";
        }
        const fecha = new Date(valor);
        if (Number.isNaN(fecha.getTime())) {
            return String(valor);
        }
        return fecha.toLocaleString("es-CO", {
            dateStyle: "short",
            timeStyle: "medium"
        });
    }

    function recortar(valor, limite) {
        const texto = String(valor || "");
        if (texto.length <= limite) {
            return texto;
        }
        return texto.slice(0, limite - 1) + "…";
    }

    function texto_resultado(valor) {
        if (valor === "exito") {
            return "Exitoso";
        }
        if (valor === "bloqueado") {
            return "Bloqueado";
        }
        if (valor === "fallo") {
            return "Fallido";
        }
        return valor || "Sin resultado";
    }

    function vista_auditoria(contenedor, contexto) {
        const estado = {
            pagina: 1,
            busqueda: "",
            resultado: "",
            desde: "",
            hasta: ""
        };

        function dibujar(datos) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.vaciar(contenedor);
            contenedor.append(
                utilidades.encabezado(
                    "Auditoría",
                    "Registro de accesos, operaciones y supervisiones administrativas.",
                    "Control y trazabilidad"
                )
            );

            const formulario = utilidades.crear(
                "form",
                "formulario_ucc barra_filtros"
            );
            formulario.setAttribute("novalidate", "");
            const busqueda = utilidades.campo({
                id: "auditoria_busqueda",
                etiqueta: "Buscar",
                nombre: "busqueda",
                valor: estado.busqueda,
                placeholder_texto: "Acción, solicitud o detalle",
                maxlength: 120
            });
            const resultado = utilidades.campo({
                id: "auditoria_resultado",
                etiqueta: "Resultado",
                nombre: "resultado",
                tipo: "select",
                valor: estado.resultado,
                placeholder: "Todos los resultados",
                opciones: [
                    { valor: "exito", texto: "Exitoso" },
                    { valor: "fallo", texto: "Fallido" },
                    { valor: "bloqueado", texto: "Bloqueado" }
                ]
            });
            const desde = utilidades.campo({
                id: "auditoria_desde",
                etiqueta: "Desde",
                nombre: "desde",
                tipo: "date",
                valor: estado.desde
            });
            const hasta = utilidades.campo({
                id: "auditoria_hasta",
                etiqueta: "Hasta",
                nombre: "hasta",
                tipo: "date",
                valor: estado.hasta
            });
            const acciones = utilidades.crear("div", "barra_filtros_acciones");
            acciones.append(
                utilidades.boton("Filtrar", "bi-search", "boton_principal", function () {
                    formulario.requestSubmit();
                })
            );
            formulario.append(
                busqueda.grupo,
                resultado.grupo,
                desde.grupo,
                hasta.grupo,
                acciones
            );
            formulario.addEventListener("submit", function (evento) {
                evento.preventDefault();
                estado.pagina = 1;
                estado.busqueda = busqueda.control.value.trim();
                estado.resultado = resultado.control.value;
                estado.desde = desde.control.value;
                estado.hasta = hasta.control.value;
                cargar();
            });
            contenedor.append(formulario);

            const filas = datos.elementos || [];
            contenedor.append(
                utilidades.tabla(
                    [
                        {
                            titulo: "Fecha",
                            valor: function (fila) {
                                return formatear_fecha_hora(fila.fecha_creacion);
                            }
                        },
                        {
                            titulo: "Acción",
                            valor: function (fila) {
                                return String(fila.accion || "").replace(/_/g, " ");
                            }
                        },
                        { titulo: "Usuario", valor: "id_usuario" },
                        { titulo: "Objetivo", valor: "id_usuario_objetivo" },
                        {
                            titulo: "Resultado",
                            valor: function (fila) {
                                return utilidades.etiqueta_estado(
                                    fila.resultado,
                                    texto_resultado(fila.resultado)
                                );
                            }
                        },
                        {
                            titulo: "Dirección IP",
                            valor: function (fila) {
                                return fila.direccion_ip || "No registrada";
                            }
                        },
                        {
                            titulo: "Detalle",
                            valor: function (fila) {
                                return recortar(fila.detalle, 90) || "Sin detalle";
                            }
                        }
                    ],
                    filas,
                    "Registro de auditoría"
                )
            );

            if (!filas.length) {
                contenedor.append(
                    utilidades.estado_vacio(
                        "No hay eventos que coincidan con los filtros.",
                        "bi-inbox"
                    )
                );
            }

            const paginacion = utilidades.crear("div", "paginacion_ucc");
            const resumen = utilidades.crear(
                "p",
                "texto_secundario",
                "Página " +
                    datos.pagina +
                    " de " +
                    datos.paginas +
                    " · " +
                    datos.total +
                    " evento(s)"
            );
            const botones = utilidades.crear("div", "grupo_botones");
            const anterior = utilidades.boton(
                "Anterior",
                "bi-arrow-left",
                "boton_claro boton_pequeno",
                function () {
                    if (estado.pagina > 1) {
                        estado.pagina -= 1;
                        cargar();
                    }
                }
            );
            anterior.disabled = estado.pagina <= 1;
            const siguiente = utilidades.boton(
                "Siguiente",
                "bi-arrow-right",
                "boton_claro boton_pequeno",
                function () {
                    if (estado.pagina < datos.paginas) {
                        estado.pagina += 1;
                        cargar();
                    }
                }
            );
            siguiente.disabled = estado.pagina >= datos.paginas;
            botones.append(anterior, siguiente);
            paginacion.append(resumen, botones);
            contenedor.append(paginacion);
        }

        async function cargar() {
            utilidades.mostrar_carga(contenedor, "Consultando auditoría...");
            try {
                const datos = await api.llamar("auditoria_listar", {
                    busqueda: estado.busqueda,
                    resultado: estado.resultado,
                    desde: estado.desde,
                    hasta: estado.hasta,
                    pagina: estado.pagina,
                    por_pagina: 25
                });
                dibujar(datos);
            } catch (error) {
                if (contexto.vigente()) {
                    utilidades.mostrar_error(
                        contenedor,
                        error.message,
                        cargar
                    );
                }
            }
        }

        cargar();
    }

    function vista_usuarios(contenedor, contexto) {
        const usuario_actual = window.app_ucc.obtener_usuario();

        function abrir_supervision(usuario, boton) {
            utilidades.ocupar_boton(boton, true, "Abriendo...");
            window.app_ucc
                .supervisar_usuario(usuario.id_usuario)
                .catch(function (error) {
                    utilidades.toast(error.message, "error");
                })
                .finally(function () {
                    utilidades.ocupar_boton(boton, false);
                });
        }

        function cambiar_estado(usuario, boton) {
            const accion = usuario.activo ? "desactivar" : "activar";
            if (!window.confirm("¿Desea " + accion + " a " + usuario.nombre + "?")) {
                return;
            }
            utilidades.ocupar_boton(boton, true, "Enviando...");
            api.llamar("admin_estado_usuario", {
                id_usuario: usuario.id_usuario,
                activo: usuario.activo ? 0 : 1
            }).then(function (respuesta) {
                utilidades.toast(respuesta.mensaje || "Listo.", "exito");
                cargar();
            }).catch(function (error) {
                utilidades.toast(error.message, "error");
                utilidades.ocupar_boton(boton, false);
            });
        }

        function restablecer(usuario, boton) {
            if (!window.confirm("¿Restablecer la contraseña de " + usuario.nombre + "? Se cerrarán sus sesiones.")) {
                return;
            }
            utilidades.ocupar_boton(boton, true, "Enviando...");
            api.llamar("admin_reset_contrasena", {
                id_usuario: usuario.id_usuario
            }).then(function (respuesta) {
                utilidades.ocupar_boton(boton, false);
                window.prompt(
                    "Contraseña temporal para " + usuario.correo + " (cópiela ahora, solo se muestra una vez):",
                    respuesta.contrasena_temporal || ""
                );
                cargar();
            }).catch(function (error) {
                utilidades.toast(error.message, "error");
                utilidades.ocupar_boton(boton, false);
            });
        }

        function panel_crear_usuario() {
            const panel = utilidades.crear("section", "panel_ucc");
            const cabeza = utilidades.crear("div", "panel_ucc_encabezado");
            const info = document.createElement("div");
            info.append(utilidades.crear("h3", "", "Crear usuario"));
            cabeza.append(info);
            const cuerpo = utilidades.crear("div", "panel_ucc_cuerpo");
            const formulario = document.createElement("form");
            formulario.className = "formulario_ucc rejilla_formulario";
            formulario.setAttribute("novalidate", "");

            const c_rol = utilidades.campo({
                id: "adm_nuevo_rol", etiqueta: "Rol", tipo: "select",
                opciones: [
                    { valor: "estudiante", texto: "Estudiante" },
                    { valor: "monitor", texto: "Monitor" },
                    { valor: "profesor", texto: "Profesor" },
                    { valor: "bienestar", texto: "Bienestar Universitario" },
                    { valor: "asesoria", texto: "Docente de Asesoría" },
                    { valor: "admin", texto: "Administrador" }
                ],
                required: true
            });
            const c_nombre = utilidades.campo({
                id: "adm_nuevo_nombre", etiqueta: "Nombre completo",
                placeholder_texto: "Nombre y apellido", required: true, maxlength: 160
            });
            const c_correo = utilidades.campo({
                id: "adm_nuevo_correo", etiqueta: "Correo", tipo: "email",
                placeholder_texto: "usuario@ucc.edu.co", required: true, maxlength: 120
            });
            const c_extra = utilidades.crear("div", "campo_ancho");
            formulario.append(c_rol.grupo, c_nombre.grupo, c_correo.grupo, c_extra);

            let estudiantes_cache = null;
            function pintar_extra() {
                utilidades.vaciar(c_extra);
                const rol = c_rol.control.value;
                if (rol === "estudiante") {
                    const prog = utilidades.campo({ id: "adm_x_programa", etiqueta: "Programa", placeholder_texto: "Ingeniería de Software" });
                    const sem = utilidades.campo({ id: "adm_x_semestre", etiqueta: "Semestre", tipo: "number", min: 1, max: 12 });
                    c_extra.append(prog.grupo, sem.grupo);
                } else if (rol === "monitor") {
                    const nota = utilidades.crear("p", "campo_ayuda", "El monitor se habilita sobre un estudiante existente.");
                    const sel = utilidades.campo({ id: "adm_x_est", etiqueta: "Estudiante base", tipo: "select", required: true });
                    const asig = utilidades.campo({
                        id: "adm_x_asig", etiqueta: "Asignatura", tipo: "select",
                        opciones: ["Programación I", "Estructuras de Datos", "Bases de Datos", "Cálculo I", "Física I", "Álgebra Lineal"],
                        required: true
                    });
                    c_extra.append(nota, sel.grupo, asig.grupo);
                    sel.control.disabled = true;
                    const pintar = function (lista) {
                        utilidades.vaciar(sel.control);
                        sel.control.append(new Option("Seleccione...", ""));
                        lista.forEach(function (e) {
                            const op = new Option(e.nombre + " · " + e.correo + (e.es_monitor ? " (ya es monitor)" : ""), e.id_estudiante);
                            op.disabled = !!e.es_monitor;
                            sel.control.append(op);
                        });
                        sel.control.disabled = false;
                    };
                    if (estudiantes_cache) { pintar(estudiantes_cache); }
                    else {
                        api.llamar("admin_estudiantes").then(function (d) {
                            if (!contexto.vigente()) { return; }
                            estudiantes_cache = d.estudiantes || [];
                            pintar(estudiantes_cache);
                        }).catch(function (e) { utilidades.toast(e.message, "error"); });
                    }
                } else if (rol === "profesor") {
                    c_extra.append(utilidades.campo({ id: "adm_x_dep", etiqueta: "Departamento", placeholder_texto: "Ingeniería de Software" }).grupo);
                } else if (rol === "bienestar" || rol === "asesoria") {
                    c_extra.append(utilidades.campo({ id: "adm_x_cargo", etiqueta: "Cargo", placeholder_texto: "Cargo institucional" }).grupo);
                }
            }
            c_rol.control.addEventListener("change", pintar_extra);
            pintar_extra();

            const barra = utilidades.crear("div", "acciones_formulario");
            const guardar = utilidades.boton("Crear cuenta", "bi-person-plus", "boton_exito");
            guardar.type = "submit";
            barra.append(guardar);
            formulario.append(barra);
            formulario.addEventListener("submit", function (evento) {
                evento.preventDefault();
                if (!formulario.checkValidity()) {
                    formulario.reportValidity();
                    return;
                }
                const datos = {
                    rol: c_rol.control.value,
                    nombre: c_nombre.control.value.trim(),
                    correo: c_correo.control.value.trim()
                };
                const mapa = {
                    adm_x_programa: "programa",
                    adm_x_semestre: "semestre",
                    adm_x_est: "id_estudiante",
                    adm_x_asig: "asignatura",
                    adm_x_dep: "departamento",
                    adm_x_cargo: "cargo"
                };
                Object.keys(mapa).forEach(function (id) {
                    const el = document.getElementById(id);
                    if (el && String(el.value).trim() !== "") {
                        datos[mapa[id]] = el.value.trim();
                    }
                });
                utilidades.ocupar_boton(guardar, true, "Creando...");
                api.llamar("admin_crear_usuario", datos).then(function (respuesta) {
                    utilidades.ocupar_boton(guardar, false);
                    formulario.reset();
                    pintar_extra();
                    window.prompt(
                        "Cuenta creada para " + respuesta.correo + ". Contraseña temporal (cópiela ahora):",
                        respuesta.contrasena_temporal || ""
                    );
                    cargar();
                }).catch(function (error) {
                    utilidades.toast(error.message, "error");
                    utilidades.ocupar_boton(guardar, false);
                });
            });
            cuerpo.append(formulario);
            panel.append(cabeza, cuerpo);
            return panel;
        }

        function dibujar(datos) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.vaciar(contenedor);
            contenedor.append(
                utilidades.encabezado(
                    "Usuarios",
                    "Consulte las cuentas del sistema y abra una supervisión auditada.",
                    "Administración de acceso"
                )
            );

            contenedor.append(panel_crear_usuario());

            const usuarios = datos.usuarios || [];
            contenedor.append(
                utilidades.tabla(
                    [
                        { titulo: "Nombre", valor: "nombre" },
                        { titulo: "Correo", valor: "correo" },
                        { titulo: "Rol", valor: "rol_texto" },
                        {
                            titulo: "Estado",
                            valor: function (usuario) {
                                return utilidades.etiqueta_estado(
                                    usuario.activo ? "activo" : "inactivo",
                                    usuario.activo ? "Activo" : "Inactivo"
                                );
                            }
                        },
                        {
                            titulo: "Creado",
                            valor: function (usuario) {
                                return formatear_fecha_hora(usuario.creado_en);
                            }
                        },
                        {
                            titulo: "Acciones",
                            valor: function (usuario) {
                                if (!es_supervisable(usuario)) {
                                    return utilidades.etiqueta_neutra(
                                        "Sin acciones"
                                    );
                                }
                                const grupo = utilidades.crear(
                                    "div", "grupo_botones"
                                );
                                const boton_ver = utilidades.boton(
                                    "Supervisar",
                                    "bi-eye",
                                    "boton_claro boton_pequeno"
                                );
                                boton_ver.addEventListener("click", function () {
                                    abrir_supervision(usuario, boton_ver);
                                });
                                const boton_estado = utilidades.boton(
                                    usuario.activo ? "Desactivar" : "Activar",
                                    usuario.activo ? "bi-x-lg" : "bi-check2",
                                    "boton_claro boton_pequeno"
                                );
                                boton_estado.addEventListener("click", function () {
                                    cambiar_estado(usuario, boton_estado);
                                });
                                const boton_reset = utilidades.boton(
                                    "Restablecer",
                                    "bi-key",
                                    "boton_claro boton_pequeno"
                                );
                                boton_reset.addEventListener("click", function () {
                                    restablecer(usuario, boton_reset);
                                });
                                grupo.append(boton_ver, boton_estado, boton_reset);
                                return grupo;
                            }
                        }
                    ],
                    usuarios,
                    "Usuarios del sistema"
                )
            );

            if (!usuarios.length) {
                contenedor.append(
                    utilidades.estado_vacio(
                        "No hay usuarios registrados.",
                        "bi-people"
                    )
                );
            }
        }

        async function cargar() {
            utilidades.mostrar_carga(contenedor, "Consultando usuarios...");
            try {
                const datos = await api.llamar("admin_usuarios");
                dibujar(datos);
            } catch (error) {
                if (contexto.vigente()) {
                    utilidades.mostrar_error(contenedor, error.message, cargar);
                }
            }
        }

        cargar();
    }

    function vista_supervision(contenedor, contexto) {
        const contexto_admin = window.app_ucc.obtener_contexto_admin();
        const usuario_actual = window.app_ucc.obtener_usuario();

        function dibujar_contexto(datos) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.vaciar(contenedor);
            contenedor.append(
                utilidades.encabezado(
                    "Supervisión de funciones",
                    "Abra los módulos del usuario seleccionado. Toda acción conserva trazabilidad.",
                    "Control administrativo"
                )
            );

            const objetivo = datos.usuario_objetivo;
            const ficha = utilidades.crear("section", "ficha_supervision");
            ficha.append(
                utilidades.lista_datos([
                    { etiqueta: "Usuario", valor: objetivo.nombre },
                    { etiqueta: "Correo", valor: objetivo.correo },
                    { etiqueta: "Rol", valor: objetivo.rol_texto },
                    { etiqueta: "Identificador", valor: objetivo.id_usuario }
                ])
            );
            const acciones = utilidades.crear("div", "ficha_supervision_acciones");
            acciones.append(
                utilidades.boton(
                    "Finalizar supervisión",
                    "bi-x-lg",
                    "boton_peligro boton_pequeno",
                    function () {
                        window.app_ucc.salir_supervision();
                    }
                )
            );
            ficha.append(acciones);
            contenedor.append(ficha);

            const modulos = datos.modulos || [];
            const rejilla = utilidades.crear("div", "rejilla_supervision");
            modulos.forEach(function (modulo) {
                const tarjeta = utilidades.crear(
                    "button",
                    "tarjeta_supervision"
                );
                tarjeta.type = "button";
                const caja_icono = utilidades.crear(
                    "span",
                    "tarjeta_supervision_icono"
                );
                caja_icono.append(
                    utilidades.icono(modulo.icono || "bi-circle")
                );
                tarjeta.append(
                    caja_icono,
                    utilidades.crear("strong", "", modulo.titulo),
                    utilidades.crear(
                        "span",
                        "texto_secundario",
                        "Abrir módulo como " + objetivo.rol_texto
                    )
                );
                tarjeta.addEventListener("click", function () {
                    window.app_ucc.abrir_modulo_objetivo(modulo.clave);
                });
                rejilla.append(tarjeta);
            });
            contenedor.append(rejilla);
        }

        function dibujar_seleccion(datos) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.vaciar(contenedor);
            contenedor.append(
                utilidades.encabezado(
                    "Supervisión de funciones",
                    "Seleccione una cuenta activa para revisar sus módulos y operar en su contexto.",
                    "Control administrativo"
                )
            );

            const usuarios = (datos.usuarios || []).filter(es_supervisable);
            const formulario = utilidades.crear("form", "formulario_ucc");
            formulario.setAttribute("novalidate", "");
            const seleccion = utilidades.campo({
                id: "supervision_usuario",
                etiqueta: "Usuario a supervisar",
                nombre: "id_usuario",
                tipo: "select",
                opciones: usuarios.map(function (usuario) {
                    return {
                        valor: usuario.id_usuario,
                        texto:
                            usuario.nombre +
                            " · " +
                            usuario.rol_texto +
                            " · " +
                            usuario.correo
                    };
                }),
                required: true
            });
            const boton = utilidades.boton(
                "Abrir supervisión",
                "bi-shield-check",
                "boton_principal",
                function () {
                    formulario.requestSubmit();
                }
            );
            formulario.append(seleccion.grupo, boton);
            formulario.addEventListener("submit", function (evento) {
                evento.preventDefault();
                if (!formulario.checkValidity()) {
                    formulario.reportValidity();
                    return;
                }
                utilidades.ocupar_boton(boton, true, "Abriendo...");
                window.app_ucc
                    .supervisar_usuario(seleccion.control.value)
                    .catch(function (error) {
                        utilidades.toast(error.message, "error");
                    })
                    .finally(function () {
                        utilidades.ocupar_boton(boton, false);
                    });
            });
            contenedor.append(formulario);

            if (!usuarios.length) {
                contenedor.append(
                    utilidades.estado_vacio(
                        "No hay otras cuentas activas para supervisar.",
                        "bi-people"
                    )
                );
            }
        }

        if (contexto_admin) {
            dibujar_contexto(contexto_admin);
            return;
        }

        utilidades.mostrar_carga(contenedor, "Cargando usuarios...");
        api.llamar("admin_usuarios")
            .then(dibujar_seleccion)
            .catch(function (error) {
                if (contexto.vigente()) {
                    utilidades.mostrar_error(
                        contenedor,
                        error.message,
                        function () {
                            vista_supervision(contenedor, contexto);
                        }
                    );
                }
            });
    }

    window.vistas_ucc.auditoria = vista_auditoria;
    window.vistas_ucc.usuarios = vista_usuarios;
    window.vistas_ucc.materias = vista_materias;
    window.vistas_ucc.supervision = vista_supervision;

    function vista_materias(contenedor, contexto) {
        function dibujar(datos) {
            if (!contexto.vigente()) {
                return;
            }
            utilidades.vaciar(contenedor);
            contenedor.append(utilidades.encabezado(
                "Materias", "Control total de la oferta académica.", "Administración académica"
            ));

            const panel = utilidades.crear("section", "panel_ucc");
            const cabeza = utilidades.crear("div", "panel_ucc_encabezado");
            const info = document.createElement("div");
            info.append(utilidades.crear("h3", "", "Crear materia"));
            cabeza.append(info);
            const cuerpo = utilidades.crear("div", "panel_ucc_cuerpo");
            const formulario = document.createElement("form");
            formulario.className = "formulario_ucc rejilla_formulario";
            formulario.setAttribute("novalidate", "");
            const c_nombre = utilidades.campo({ id: "mat_nombre", etiqueta: "Nombre", placeholder_texto: "Cálculo I", required: true, maxlength: 160 });
            const c_codigo = utilidades.campo({ id: "mat_codigo", etiqueta: "Código", placeholder_texto: "CAL101", required: true, maxlength: 40 });
            const c_periodo = utilidades.campo({ id: "mat_periodo", etiqueta: "Periodo", placeholder_texto: "2026-2", maxlength: 40 });
            const c_prof = utilidades.campo({ id: "mat_prof", etiqueta: "Profesor", tipo: "select", required: true });
            formulario.append(c_nombre.grupo, c_codigo.grupo, c_periodo.grupo, c_prof.grupo);
            const barra = utilidades.crear("div", "acciones_formulario");
            const guardar = utilidades.boton("Crear materia", "bi-plus-circle", "boton_exito");
            guardar.type = "submit";
            barra.append(guardar);
            formulario.append(barra);
            formulario.addEventListener("submit", function (evento) {
                evento.preventDefault();
                if (!formulario.checkValidity()) {
                    formulario.reportValidity();
                    return;
                }
                utilidades.ocupar_boton(guardar, true, "Creando...");
                api.llamar("admin_crear_curso", {
                    nombre: c_nombre.control.value.trim(),
                    codigo: c_codigo.control.value.trim(),
                    periodo: c_periodo.control.value.trim() || "2026-2",
                    id_profesor: c_prof.control.value
                }).then(function (respuesta) {
                    utilidades.toast(respuesta.mensaje || "Materia creada.", "exito");
                    cargar();
                }).catch(function (error) {
                    utilidades.toast(error.message, "error");
                    utilidades.ocupar_boton(guardar, false);
                });
            });
            cuerpo.append(formulario);
            panel.append(cabeza, cuerpo);
            contenedor.append(panel);

            api.llamar("admin_usuarios").then(function (u) {
                if (!contexto.vigente()) { return; }
                const profes = (u.usuarios || []).filter(function (x) { return x.rol === "profesor" && x.activo; });
                utilidades.vaciar(c_prof.control);
                c_prof.control.append(new Option("Seleccione...", ""));
                profes.forEach(function (p) {
                    c_prof.control.append(new Option(p.nombre + " · " + p.correo, p.id_perfil));
                });
            }).catch(function (error) { utilidades.toast(error.message, "error"); });

            const cursos = datos.cursos || [];
            contenedor.append(utilidades.tabla([
                { titulo: "Materia", valor: "nombre" },
                { titulo: "Código", valor: "codigo" },
                { titulo: "Periodo", valor: "periodo" },
                { titulo: "Profesor", valor: "profesor" }
            ], cursos, "Materias registradas"));
            if (!cursos.length) {
                contenedor.append(utilidades.estado_vacio("No hay materias registradas.", "bi-journal-bookmark"));
            }
        }

        async function cargar() {
            utilidades.mostrar_carga(contenedor, "Consultando materias...");
            try {
                dibujar(await api.llamar("admin_cursos"));
            } catch (error) {
                if (contexto.vigente()) {
                    utilidades.mostrar_error(contenedor, error.message, cargar);
                }
            }
        }

        cargar();
    }
})();

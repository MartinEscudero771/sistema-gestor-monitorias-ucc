window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    function tabla_monitorias(monitorias, titulo) {
        const columnas = [
            {
                titulo: "Asignatura",
                valor: "asignatura",
                clase: "celda_principal"
            },
            { titulo: "Monitor", valor: "monitor" },
            { titulo: "Fecha", valor: "fecha" },
            {
                titulo: "Horario",
                valor: function (fila) {
                    return fila.hora_inicio + " - " + fila.hora_fin;
                }
            },
            { titulo: "Modalidad", valor: "modalidad" },
            { titulo: "Lugar o enlace", valor: "lugar" },
            {
                titulo: "Estado",
                valor: function (fila) {
                    return utilidades.etiqueta_estado(
                        fila.estado,
                        fila.estado_texto
                    );
                }
            }
        ];
        return utilidades.tabla(columnas, monitorias, titulo);
    }

    function dibujar_monitorias(contenedor, datos) {
        utilidades.vaciar(contenedor);
        const acciones = utilidades.boton(
            "Solicitar monitoría",
            "bi-plus-circle",
            "boton_principal"
        );
        acciones.addEventListener("click", function () {
            window.app_ucc.abrir_modulo("solicitar_monitoria");
        });
        contenedor.append(
            utilidades.encabezado(
                "Mis monitorías",
                "Consulte las sesiones de acompañamiento programadas y su historial.",
                "Acompañamiento académico",
                acciones
            )
        );

        const proximas = datos.proximas || [];
        const historial = datos.historial || [];

        const seccion_proximas = utilidades.crear("section", "seccion_ucc");
        const encabezado_proximas = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_proximas = document.createElement("div");
        texto_proximas.append(
            utilidades.crear("h3", "", "Próximas sesiones")
        );
        encabezado_proximas.append(texto_proximas);
        seccion_proximas.append(encabezado_proximas);
        if (proximas.length === 0) {
            seccion_proximas.append(
                utilidades.estado_vacio(
                    "No tiene monitorías próximas programadas.",
                    "bi-calendar-x"
                )
            );
        } else {
            seccion_proximas.append(
                tabla_monitorias(proximas, "Próximas monitorías")
            );
        }

        const seccion_historial = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_historial = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_historial = document.createElement("div");
        texto_historial.append(
            utilidades.crear("h3", "", "Historial")
        );
        encabezado_historial.append(texto_historial);
        seccion_historial.append(encabezado_historial);
        if (historial.length === 0) {
            seccion_historial.append(
                utilidades.estado_vacio(
                    "Todavía no hay monitorías en su historial.",
                    "bi-clock-history"
                )
            );
        } else {
            seccion_historial.append(
                tabla_monitorias(historial, "Historial de monitorías")
            );
        }

        contenedor.append(seccion_proximas, seccion_historial);
    }

    async function vista_mis_monitorias(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "estudiante_monitorias",
            contexto,
            function (datos) {
                dibujar_monitorias(contenedor, datos);
            }
        );
    }

    function tabla_solicitudes(solicitudes) {
        const columnas = [
            {
                titulo: "Asignatura",
                valor: "asignatura",
                clase: "celda_principal"
            },
            {
                titulo: "Tema",
                valor: "tema",
                clase: "celda_secundaria"
            },
            {
                titulo: "Fecha preferida",
                valor: function (fila) {
                    return fila.fecha_preferida + " · " + fila.hora_preferida;
                }
            },
            {
                titulo: "Estado",
                valor: function (fila) {
                    return utilidades.etiqueta_estado(
                        fila.estado,
                        fila.estado_texto
                    );
                }
            },
            {
                titulo: "Respuesta",
                valor: function (fila) {
                    return fila.respuesta || "Sin respuesta";
                },
                clase: "celda_secundaria"
            },
            { titulo: "Solicitada", valor: "fecha_creacion" }
        ];
        return utilidades.tabla(columnas, solicitudes, "Historial de solicitudes");
    }

    function dibujar_solicitudes(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Solicitar monitoría",
                "Registre la asignatura, el tema y el horario en el que necesita apoyo académico.",
                "Solicitud de apoyo"
            )
        );

        const distribucion = utilidades.crear("div", "rejilla_principal");
        const panel_formulario = utilidades.crear("section", "panel_ucc");
        const encabezado_formulario = utilidades.crear(
            "div",
            "panel_ucc_encabezado"
        );
        const texto_formulario = document.createElement("div");
        texto_formulario.append(
            utilidades.crear("h3", "", "Nueva solicitud")
        );
        encabezado_formulario.append(texto_formulario);

        const cuerpo_formulario = utilidades.crear(
            "div",
            "panel_ucc_cuerpo"
        );
        const formulario = document.createElement("form");
        formulario.className = "formulario_ucc";
        formulario.noValidate = false;

        const rejilla = utilidades.crear("div", "rejilla_formulario");
        const asignatura = utilidades.campo({
            id: "solicitud_asignatura",
            etiqueta: "Asignatura",
            tipo: "select",
            opciones: datos.asignaturas || [],
            placeholder: "Seleccione una asignatura",
            required: true
        });
        const fecha = utilidades.campo({
            id: "solicitud_fecha",
            etiqueta: "Fecha preferida",
            tipo: "date",
            min: datos.fecha_minima,
            max: datos.fecha_maxima,
            required: true
        });
        const hora = utilidades.campo({
            id: "solicitud_hora",
            etiqueta: "Hora preferida",
            tipo: "time",
            min: "06:00",
            max: "21:00",
            step: "60",
            required: true
        });
        const tema = utilidades.campo({
            id: "solicitud_tema",
            etiqueta: "Tema de la monitoría",
            tipo: "textarea",
            filas: 4,
            minlength: 5,
            maxlength: 300,
            placeholder_texto:
                "Describa brevemente el tema o la dificultad que necesita resolver.",
            ayuda: "Entre 5 y 300 caracteres.",
            required: true,
            ancho: true
        });
        rejilla.append(
            asignatura.grupo,
            fecha.grupo,
            hora.grupo,
            tema.grupo
        );

        const mensaje = utilidades.crear("p", "mensaje_validacion");
        mensaje.hidden = true;
        const acciones = utilidades.crear("div", "acciones_formulario");
        const enviar = utilidades.boton(
            "Enviar solicitud",
            "bi-send",
            "boton_principal"
        );
        enviar.type = "submit";
        acciones.append(mensaje, enviar);
        formulario.append(rejilla, acciones);
        cuerpo_formulario.append(formulario);
        panel_formulario.append(encabezado_formulario, cuerpo_formulario);

        formulario.addEventListener("submit", async function (evento) {
            evento.preventDefault();
            mensaje.hidden = true;
            if (!formulario.reportValidity()) {
                return;
            }
            utilidades.ocupar_boton(enviar, true, "Enviando...");
            try {
                const respuesta = await window.api_ucc.llamar(
                    "estudiante_guardar_solicitud",
                    {
                        asignatura: asignatura.control.value,
                        tema: tema.control.value.trim(),
                        fecha_preferida: fecha.control.value,
                        hora_preferida: hora.control.value
                    }
                );
                if (!contexto.vigente()) {
                    return;
                }
                utilidades.toast(
                    respuesta.mensaje || "La solicitud fue enviada.",
                    "exito"
                );
                dibujar_solicitudes(contenedor, respuesta, contexto);
            } catch (error) {
                if (!contexto.vigente()) {
                    return;
                }
                mensaje.textContent = error.message;
                mensaje.hidden = false;
                utilidades.toast(error.message, "error");
                utilidades.ocupar_boton(enviar, false);
            }
        });

        const panel_historial = utilidades.crear("section", "seccion_ucc");
        const encabezado_historial = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_historial = document.createElement("div");
        texto_historial.append(
            utilidades.crear("h3", "", "Mis solicitudes")
        );
        encabezado_historial.append(texto_historial);
        panel_historial.append(encabezado_historial);
        if ((datos.solicitudes || []).length === 0) {
            panel_historial.append(
                utilidades.estado_vacio(
                    "Todavía no ha registrado solicitudes de monitoría.",
                    "bi-chat-left-text"
                )
            );
        } else {
            panel_historial.append(tabla_solicitudes(datos.solicitudes));
        }

        distribucion.append(panel_formulario, panel_historial);
        contenedor.append(distribucion);
    }

    async function vista_solicitar_monitoria(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "estudiante_solicitudes",
            contexto,
            function (datos) {
                dibujar_solicitudes(contenedor, datos, contexto);
            }
        );
    }

    function crear_selector_horario(datos) {
        const contenedor = utilidades.crear(
            "div",
            "selector_horario_contenedor"
        );
        const tabla = utilidades.crear("table", "selector_horario");
        const cabeza = document.createElement("thead");
        const fila_cabeza = document.createElement("tr");
        fila_cabeza.append(utilidades.crear("th", "", "Día"));
        (datos.bloques || []).forEach(function (bloque) {
            const celda = document.createElement("th");
            celda.scope = "col";
            celda.textContent = bloque.nombre;
            fila_cabeza.append(celda);
        });
        cabeza.append(fila_cabeza);

        const cuerpo = document.createElement("tbody");
        const selecciones = [];
        const horario_actual = datos.horario_actual || [];

        (datos.dias || []).forEach(function (dia) {
            const fila = document.createElement("tr");
            fila.append(utilidades.crear("th", "", dia));
            (datos.bloques || []).forEach(function (bloque) {
                const celda = document.createElement("td");
                const grupo = utilidades.crear("div", "form-check");
                const control = document.createElement("input");
                control.type = "checkbox";
                control.className = "form-check-input";
                control.id =
                    "horario_" +
                    dia.toLowerCase().replace(/\s+/g, "_") +
                    "_" +
                    bloque.clave;
                control.setAttribute(
                    "aria-label",
                    dia + ", " + bloque.nombre
                );
                const seleccionado = horario_actual.some(function (item) {
                    return (
                        item.dia === dia &&
                        item.inicio === bloque.inicio &&
                        item.fin === bloque.fin
                    );
                });
                control.checked = seleccionado;
                grupo.append(control);
                celda.append(grupo);
                fila.append(celda);
                selecciones.push({
                    dia: dia,
                    bloque: bloque,
                    control: control
                });
            });
            cuerpo.append(fila);
        });

        tabla.append(cabeza, cuerpo);
        contenedor.append(tabla);
        return {
            contenedor: contenedor,
            selecciones: selecciones
        };
    }

    function dibujar_postulacion(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Ser monitor",
                "Conozca los requisitos y registre su disponibilidad para acompañar a otros estudiantes.",
                "Postulación"
            )
        );

        const estudiante = datos.estudiante || {};
        const rejilla_info = utilidades.crear("div", "rejilla_tres_columnas");
        const tarjetas = [
            {
                titulo: "Promedio acumulado",
                valor: Number(estudiante.promedio || 0).toFixed(1),
                detalle: "Requisito: mayor a 4.0",
                icono: "bi-graph-up-arrow",
                tipo: estudiante.promedio > 4 ? "verde" : "rojo"
            },
            {
                titulo: "Materias reprobadas",
                valor: estudiante.materias_reprobadas || 0,
                detalle: "Requisito: cero materias",
                icono: "bi-journal-x",
                tipo:
                    estudiante.materias_reprobadas === 0
                        ? "verde"
                        : "rojo"
            },
            {
                titulo: "Semestre actual",
                valor: estudiante.semestre || "—",
                detalle: estudiante.programa || "Programa académico",
                icono: "bi-mortarboard",
                tipo: "azul"
            }
        ];
        tarjetas.forEach(function (tarjeta) {
            rejilla_info.append(utilidades.tarjeta_metrica(tarjeta));
        });
        contenedor.append(rejilla_info);

        if ((datos.motivos || []).length > 0) {
            const aviso = utilidades.alerta(
                "Por el momento no cumple todos los requisitos: " +
                    datos.motivos.join(" "),
                "alerta"
            );
            contenedor.append(aviso);
        }

        if (datos.monitor_activo) {
            contenedor.append(
                utilidades.alerta(
                    "Usted ya es estudiante monitor activo. Puede consultar sus tutorías en el módulo correspondiente.",
                    "exito"
                )
            );
        } else if (datos.postulacion) {
            const panel_estado = utilidades.crear("div", "panel_ucc");
            const cuerpo_estado = utilidades.crear(
                "div",
                "panel_ucc_cuerpo"
            );
            cuerpo_estado.append(
                utilidades.crear(
                    "p",
                    "etiqueta_superior",
                    "Última postulación"
                ),
                utilidades.crear(
                    "h3",
                    "",
                    datos.postulacion.asignatura
                ),
                utilidades.etiqueta_estado(
                    datos.postulacion.estado,
                    datos.postulacion.estado_texto
                )
            );
            cuerpo_estado.append(
                utilidades.lista_datos([
                    {
                        etiqueta: "Fecha",
                        valor: datos.postulacion.fecha_texto
                    },
                    {
                        etiqueta: "Motivo del rechazo",
                        valor:
                            datos.postulacion.motivo_rechazo ||
                            "No aplica"
                    }
                ])
            );
            if (datos.postulacion.estado === "pendiente") {
                cuerpo_estado.append(
                    utilidades.alerta(
                        "Su postulación está siendo revisada por Bienestar Universitario.",
                        "informacion",
                        false
                    )
                );
            }
            panel_estado.append(cuerpo_estado);
            contenedor.append(panel_estado);
        }

        const puede_postular =
            datos.elegible &&
            !datos.monitor_activo &&
            (!datos.postulacion || datos.postulacion.estado === "rechazada");

        if (!puede_postular) {
            return;
        }

        const panel = utilidades.crear("section", "panel_ucc");
        const encabezado_panel = utilidades.crear(
            "div",
            "panel_ucc_encabezado"
        );
        const texto_panel = document.createElement("div");
        texto_panel.append(
            utilidades.crear("h3", "", "Nueva postulación")
        );
        encabezado_panel.append(texto_panel);
        const cuerpo = utilidades.crear("div", "panel_ucc_cuerpo");
        const formulario = document.createElement("form");
        formulario.className = "formulario_ucc";

        const asignatura = utilidades.campo({
            id: "postulacion_asignatura",
            etiqueta: "Asignatura para acompañar",
            tipo: "select",
            opciones: datos.asignaturas || [],
            placeholder: "Seleccione una asignatura",
            required: true,
            ancho: true
        });
        const selector = crear_selector_horario(datos);
        const grupo_horario = utilidades.crear("div", "campo_formulario campo_ancho");
        grupo_horario.append(
            utilidades.crear("p", "form-label", "Disponibilidad semanal"),
            selector.contenedor,
            utilidades.crear(
                "p",
                "campo_ayuda",
                "Marque al menos un bloque. Las tutorías se programan de lunes a viernes."
            )
        );

        const rejilla = utilidades.crear("div", "rejilla_formulario");
        rejilla.append(asignatura.grupo, grupo_horario);

        const mensaje = utilidades.crear("p", "mensaje_validacion");
        mensaje.hidden = true;
        const acciones = utilidades.crear("div", "acciones_formulario");
        const enviar = utilidades.boton(
            "Enviar postulación",
            "bi-send-check",
            "boton_principal"
        );
        enviar.type = "submit";
        acciones.append(mensaje, enviar);
        formulario.append(rejilla, acciones);
        cuerpo.append(formulario);
        panel.append(encabezado_panel, cuerpo);
        contenedor.append(panel);

        formulario.addEventListener("submit", async function (evento) {
            evento.preventDefault();
            mensaje.hidden = true;
            if (!formulario.reportValidity()) {
                return;
            }

            const horario = selector.selecciones
                .filter(function (seleccion) {
                    return seleccion.control.checked;
                })
                .map(function (seleccion) {
                    return {
                        dia: seleccion.dia,
                        inicio: seleccion.bloque.inicio,
                        fin: seleccion.bloque.fin
                    };
                });

            if (horario.length === 0) {
                mensaje.textContent =
                    "Seleccione al menos un bloque de disponibilidad.";
                mensaje.hidden = false;
                selector.contenedor.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
                return;
            }

            utilidades.ocupar_boton(enviar, true, "Enviando...");
            try {
                const respuesta = await window.api_ucc.llamar(
                    "estudiante_guardar_postulacion",
                    {
                        asignatura: asignatura.control.value,
                        horario: horario
                    }
                );
                if (!contexto.vigente()) {
                    return;
                }
                utilidades.toast(
                    respuesta.mensaje || "La postulación fue enviada.",
                    "exito"
                );
                dibujar_postulacion(contenedor, respuesta, contexto);
            } catch (error) {
                if (!contexto.vigente()) {
                    return;
                }
                mensaje.textContent = error.message;
                mensaje.hidden = false;
                utilidades.toast(error.message, "error");
                utilidades.ocupar_boton(enviar, false);
            }
        });
    }

    async function vista_postular_monitor(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "estudiante_postulacion",
            contexto,
            function (datos) {
                dibujar_postulacion(contenedor, datos, contexto);
            }
        );
    }

    window.vistas_ucc.mis_monitorias = vista_mis_monitorias;
    window.vistas_ucc.solicitar_monitoria = vista_solicitar_monitoria;
    window.vistas_ucc.postular_monitor = vista_postular_monitor;
})();

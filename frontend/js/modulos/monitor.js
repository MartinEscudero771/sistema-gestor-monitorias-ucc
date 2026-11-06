window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    function fecha_mas_dias(dias) {
        const fecha = new Date();
        fecha.setDate(fecha.getDate() + Number(dias));
        const zona = new Date(
            fecha.getTime() - fecha.getTimezoneOffset() * 60000
        );
        return zona.toISOString().slice(0, 10);
    }

    function tabla_tutorias(tutorias, titulo) {
        const columnas = [
            {
                titulo: "Estudiante",
                valor: "estudiante",
                clase: "celda_principal"
            },
            { titulo: "Asignatura", valor: "asignatura" },
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
        return utilidades.tabla(columnas, tutorias, titulo);
    }

    function dibujar_tutorias(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Mis tutorías",
                "Programe nuevas sesiones y consulte el estado de los acompañamientos asignados.",
                "Agenda del monitor"
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
            utilidades.crear("h3", "", "Programar una tutoría")
        );
        encabezado_formulario.append(texto_formulario);
        const cuerpo_formulario = utilidades.crear(
            "div",
            "panel_ucc_cuerpo"
        );

        if ((datos.asignaciones || []).length === 0) {
            cuerpo_formulario.append(
                utilidades.estado_vacio(
                    "No tiene estudiantes asignados para programar tutorías.",
                    "bi-person-x",
                    true
                )
            );
        } else {
            const formulario = document.createElement("form");
            formulario.className = "formulario_ucc";
            const rejilla = utilidades.crear("div", "rejilla_formulario");

            const asignacion = utilidades.campo({
                id: "tutoria_asignacion",
                etiqueta: "Estudiante y asignatura",
                tipo: "select",
                opciones: datos.asignaciones.map(function (item) {
                    return {
                        valor: item.id_asignacion,
                        texto:
                            item.estudiante +
                            " · " +
                            item.asignatura +
                            " · " +
                            Number(item.promedio).toFixed(1)
                    };
                }),
                placeholder: "Seleccione un acompañamiento",
                required: true,
                ancho: true
            });
            const fecha = utilidades.campo({
                id: "tutoria_fecha",
                etiqueta: "Fecha",
                tipo: "date",
                min: datos.fecha_minima,
                max: fecha_mas_dias(90),
                required: true
            });
            const modalidad = utilidades.campo({
                id: "tutoria_modalidad",
                etiqueta: "Modalidad",
                tipo: "select",
                opciones: [
                    { valor: "presencial", texto: "Presencial" },
                    { valor: "virtual", texto: "Virtual" }
                ],
                placeholder: "Seleccione la modalidad",
                required: true
            });
            const hora_inicio = utilidades.campo({
                id: "tutoria_hora_inicio",
                etiqueta: "Hora de inicio",
                tipo: "time",
                min: "06:00",
                max: "21:30",
                step: "60",
                required: true
            });
            const hora_fin = utilidades.campo({
                id: "tutoria_hora_fin",
                etiqueta: "Hora de fin",
                tipo: "time",
                min: "06:30",
                max: "22:00",
                step: "60",
                required: true
            });
            const lugar = utilidades.campo({
                id: "tutoria_lugar",
                etiqueta: "Aula o enlace",
                tipo: "text",
                minlength: 3,
                maxlength: 500,
                placeholder_texto: "Ejemplo: Aula 204",
                ayuda: "Para una tutoría presencial escriba el aula; para una virtual, un enlace http o https.",
                required: true,
                ancho: true
            });

            modalidad.control.addEventListener("change", function () {
                const etiqueta = lugar.grupo.querySelector("label");
                const ayuda = lugar.grupo.querySelector(".campo_ayuda");
                if (modalidad.control.value === "virtual") {
                    etiqueta.textContent = "Enlace de la videollamada";
                    lugar.control.placeholder = "https://ejemplo.com/reunion";
                    ayuda.textContent =
                        "Escriba un enlace completo que inicie con http:// o https://.";
                } else {
                    etiqueta.textContent = "Aula o enlace";
                    lugar.control.placeholder = "Ejemplo: Aula 204";
                    ayuda.textContent =
                        "Para una tutoría presencial escriba el aula; para una virtual, un enlace http o https.";
                }
            });

            rejilla.append(
                asignacion.grupo,
                fecha.grupo,
                modalidad.grupo,
                hora_inicio.grupo,
                hora_fin.grupo,
                lugar.grupo
            );

            const mensaje = utilidades.crear("p", "mensaje_validacion");
            mensaje.hidden = true;
            const acciones = utilidades.crear(
                "div",
                "acciones_formulario"
            );
            const enviar = utilidades.boton(
                "Programar tutoría",
                "bi-calendar-plus",
                "boton_principal"
            );
            enviar.type = "submit";
            acciones.append(mensaje, enviar);
            formulario.append(rejilla, acciones);
            cuerpo_formulario.append(formulario);
            panel_formulario.append(
                encabezado_formulario,
                cuerpo_formulario
            );

            formulario.addEventListener("submit", async function (evento) {
                evento.preventDefault();
                mensaje.hidden = true;
                if (!formulario.reportValidity()) {
                    return;
                }
                utilidades.ocupar_boton(enviar, true, "Programando...");
                try {
                    const respuesta = await window.api_ucc.llamar(
                        "monitor_guardar_tutoria",
                        {
                            id_asignacion: asignacion.control.value,
                            fecha: fecha.control.value,
                            hora_inicio: hora_inicio.control.value,
                            hora_fin: hora_fin.control.value,
                            modalidad: modalidad.control.value,
                            aula_enlace: lugar.control.value.trim()
                        }
                    );
                    if (!contexto.vigente()) {
                        return;
                    }
                    utilidades.toast(
                        respuesta.mensaje || "La tutoría fue programada.",
                        "exito"
                    );
                    dibujar_tutorias(contenedor, respuesta, contexto);
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

        if ((datos.asignaciones || []).length === 0) {
            panel_formulario.append(
                encabezado_formulario,
                cuerpo_formulario
            );
        }

        const panel_lateral = utilidades.crear("aside", "seccion_ucc");
        const tarjeta_horario = utilidades.crear(
            "div",
            "tarjeta_detalle"
        );
        tarjeta_horario.append(
            utilidades.crear("p", "etiqueta_superior", "Mi disponibilidad"),
            utilidades.crear("h4", "", "Horario registrado"),
            utilidades.crear(
                "p",
                "",
                datos.horario_texto || "Sin horario registrado"
            )
        );

        const tarjeta_asignados = utilidades.crear(
            "div",
            "tarjeta_detalle"
        );
        tarjeta_asignados.append(
            utilidades.crear("p", "etiqueta_superior", "Acompañamientos"),
            utilidades.crear(
                "h4",
                "",
                (datos.asignaciones || []).length + " estudiante(s) asignado(s)"
            )
        );
        if ((datos.asignaciones || []).length === 0) {
            tarjeta_asignados.append(
                utilidades.crear(
                    "p",
                    "",
                    "No tiene estudiantes activos en este momento."
                )
            );
        } else {
            const lista = utilidades.crear("div", "lista_datos");
            datos.asignaciones.forEach(function (item) {
                const fila = document.createElement("div");
                const nombre = document.createElement("span");
                nombre.append(
                    utilidades.crear("strong", "", item.estudiante),
                    utilidades.crear(
                        "small",
                        "texto_secundario",
                        item.asignatura
                    )
                );
                fila.append(nombre);
                lista.append(fila);
            });
            tarjeta_asignados.append(lista);
        }
        panel_lateral.append(tarjeta_horario, tarjeta_asignados);
        distribucion.append(panel_formulario, panel_lateral);
        contenedor.append(distribucion);

        const seccion_proximas = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_proximas = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_proximas = document.createElement("div");
        texto_proximas.append(
            utilidades.crear("h3", "", "Próximas tutorías")
        );
        encabezado_proximas.append(texto_proximas);
        seccion_proximas.append(encabezado_proximas);
        if ((datos.proximas || []).length === 0) {
            seccion_proximas.append(
                utilidades.estado_vacio(
                    "No tiene tutorías próximas.",
                    "bi-calendar-x"
                )
            );
        } else {
            seccion_proximas.append(
                tabla_tutorias(datos.proximas, "Próximas tutorías")
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
        if ((datos.historial || []).length === 0) {
            seccion_historial.append(
                utilidades.estado_vacio(
                    "Todavía no hay tutorías en su historial.",
                    "bi-clock-history"
                )
            );
        } else {
            seccion_historial.append(
                tabla_tutorias(datos.historial, "Historial de tutorías")
            );
        }

        contenedor.append(seccion_proximas, seccion_historial);
    }

    async function vista_mis_tutorias(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "monitor_tutorias",
            contexto,
            function (datos) {
                dibujar_tutorias(contenedor, datos, contexto);
            }
        );
    }

    function dibujar_asignados(contenedor, datos) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Estudiantes asignados",
                "Estos son los estudiantes que Asesoría asignó a su acompañamiento.",
                "Acompañamiento activo"
            )
        );

        const asignaciones = datos.asignaciones || [];
        if (asignaciones.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No tiene estudiantes asignados en este momento.",
                    "bi-people"
                )
            );
            return;
        }

        const columnas = [
            {
                titulo: "Estudiante",
                valor: function (fila) {
                    const contenedor_nombre = document.createElement("div");
                    contenedor_nombre.append(
                        utilidades.crear(
                            "div",
                            "celda_principal",
                            fila.estudiante
                        ),
                        utilidades.crear(
                            "div",
                            "celda_secundaria",
                            fila.programa
                        )
                    );
                    return contenedor_nombre;
                }
            },
            { titulo: "Asignatura", valor: "asignatura" },
            {
                titulo: "Promedio",
                valor: function (fila) {
                    return Number(fila.promedio).toFixed(1);
                }
            },
            { titulo: "Profesor", valor: "profesor" },
            {
                titulo: "Motivo",
                valor: "motivo",
                clase: "celda_secundaria"
            },
            { titulo: "Sesiones", valor: "total_sesiones" },
            { titulo: "Informes", valor: "total_informes" },
            { titulo: "Asignado", valor: "fecha_asignacion" }
        ];
        contenedor.append(
            utilidades.tabla(
                columnas,
                asignaciones,
                "Estudiantes asignados al monitor"
            )
        );

        const observaciones = asignaciones.filter(function (fila) {
            return fila.observaciones;
        });
        if (observaciones.length > 0) {
            const seccion = utilidades.crear("section", "seccion_ucc");
            const titulo = document.createElement("div");
            titulo.className = "seccion_encabezado";
            const texto = document.createElement("div");
            texto.append(
                utilidades.crear("h3", "", "Observaciones de Asesoría")
            );
            titulo.append(texto);
            seccion.append(titulo);
            const lista = utilidades.crear(
                "div",
                "lista_tarjetas lista_tarjetas_una"
            );
            observaciones.forEach(function (fila) {
                const tarjeta = utilidades.crear(
                    "div",
                    "tarjeta_detalle"
                );
                tarjeta.append(
                    utilidades.crear(
                        "h4",
                        "",
                        fila.estudiante + " · " + fila.asignatura
                    ),
                    utilidades.crear("p", "", fila.observaciones)
                );
                lista.append(tarjeta);
            });
            seccion.append(lista);
            contenedor.append(seccion);
        }
    }

    async function vista_asignados(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "monitor_asignados",
            contexto,
            function (datos) {
                dibujar_asignados(contenedor, datos);
            }
        );
    }

    function dibujar_informes(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Registrar horas",
                "Reporte las horas de las tutorías finalizadas. El profesor y Bienestar validarán el informe.",
                "Informe de horas"
            )
        );

        const horas = Number(datos.horas_semana) || 0;
        const maximo = Number(datos.max_horas_semanales) || 0;
        const porcentaje = maximo > 0 ? Math.min(100, (horas / maximo) * 100) : 0;
        const panel_horas = utilidades.crear("div", "panel_ucc");
        const cuerpo_horas = utilidades.crear("div", "panel_ucc_cuerpo");
        const resumen = utilidades.crear("div", "resumen_horas");
        const texto = utilidades.crear("div", "resumen_horas_texto");
        const valor = document.createElement("span");
        valor.append(
            utilidades.crear("strong", "", horas.toFixed(1)),
            document.createTextNode(" de " + maximo + " horas esta semana")
        );
        texto.append(
            utilidades.crear(
                "span",
                "texto_secundario",
                "Avance semanal permitido"
            ),
            valor
        );
        const barra = utilidades.crear("div", "barra_progreso");
        const progreso = utilidades.crear(
            "div",
            "barra_progreso_valor" +
                (porcentaje >= 100 ? " tipo_alerta" : "")
        );
        progreso.style.width = porcentaje + "%";
        progreso.setAttribute("aria-hidden", "true");
        barra.append(progreso);
        resumen.append(texto, barra);
        cuerpo_horas.append(resumen);
        panel_horas.append(cuerpo_horas);
        contenedor.append(panel_horas);

        const panel_reporte = utilidades.crear("section", "panel_ucc");
        const encabezado_reporte = utilidades.crear(
            "div",
            "panel_ucc_encabezado"
        );
        const texto_reporte = document.createElement("div");
        texto_reporte.append(
            utilidades.crear("h3", "", "Nuevo informe")
        );
        encabezado_reporte.append(texto_reporte);
        const cuerpo_reporte = utilidades.crear(
            "div",
            "panel_ucc_cuerpo"
        );

        if ((datos.sesiones || []).length === 0) {
            cuerpo_reporte.append(
                utilidades.estado_vacio(
                    "No hay tutorías finalizadas pendientes de reportar.",
                    "bi-clipboard-check",
                    true
                )
            );
        } else {
            const formulario = document.createElement("form");
            formulario.className = "formulario_ucc";
            const rejilla = utilidades.crear("div", "rejilla_formulario");
            const sesion = utilidades.campo({
                id: "informe_sesion",
                etiqueta: "Tutoría finalizada",
                tipo: "select",
                opciones: datos.sesiones.map(function (item) {
                    return {
                        valor: item.id_monitoria,
                        texto:
                            item.fecha +
                            " · " +
                            item.asignatura +
                            " · " +
                            item.estudiante +
                            " · " +
                            item.hora_inicio +
                            " - " +
                            item.hora_fin
                    };
                }),
                placeholder: "Seleccione la tutoría",
                required: true,
                ancho: true
            });
            const cantidad = utilidades.campo({
                id: "informe_horas",
                etiqueta: "Cantidad de horas",
                tipo: "number",
                min: "0.5",
                max: "4",
                step: "0.5",
                required: true,
                ayuda: "Entre 0.5 y 4 horas, en intervalos de media hora."
            });
            const estudiantes = utilidades.campo({
                id: "informe_estudiantes",
                etiqueta: "Estudiantes atendidos",
                tipo: "text",
                minlength: 3,
                maxlength: 500,
                placeholder_texto: "Nombre o descripción de los asistentes",
                required: true
            });
            const actividades = utilidades.campo({
                id: "informe_actividades",
                etiqueta: "Actividades realizadas",
                tipo: "textarea",
                filas: 4,
                minlength: 10,
                maxlength: 1000,
                placeholder_texto:
                    "Describa los temas trabajados y las actividades desarrolladas.",
                ayuda: "Entre 10 y 1000 caracteres.",
                required: true,
                ancho: true
            });
            rejilla.append(
                sesion.grupo,
                cantidad.grupo,
                estudiantes.grupo,
                actividades.grupo
            );
            const mensaje = utilidades.crear("p", "mensaje_validacion");
            mensaje.hidden = true;
            const acciones = utilidades.crear(
                "div",
                "acciones_formulario"
            );
            const enviar = utilidades.boton(
                "Enviar informe",
                "bi-send-check",
                "boton_principal"
            );
            enviar.type = "submit";
            acciones.append(mensaje, enviar);
            formulario.append(rejilla, acciones);
            cuerpo_reporte.append(formulario);
            panel_reporte.append(encabezado_reporte, cuerpo_reporte);

            formulario.addEventListener("submit", async function (evento) {
                evento.preventDefault();
                mensaje.hidden = true;
                if (!formulario.reportValidity()) {
                    return;
                }
                utilidades.ocupar_boton(enviar, true, "Enviando...");
                try {
                    const respuesta = await window.api_ucc.llamar(
                        "monitor_guardar_informe",
                        {
                            id_monitoria: sesion.control.value,
                            cantidad_horas: cantidad.control.value,
                            actividades: actividades.control.value.trim(),
                            estudiantes_atendidos:
                                estudiantes.control.value.trim()
                        }
                    );
                    if (!contexto.vigente()) {
                        return;
                    }
                    utilidades.toast(
                        respuesta.mensaje || "El informe fue enviado.",
                        "exito"
                    );
                    dibujar_informes(contenedor, respuesta, contexto);
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

        if ((datos.sesiones || []).length === 0) {
            panel_reporte.append(encabezado_reporte, cuerpo_reporte);
        }
        contenedor.append(panel_reporte);

        const seccion = utilidades.crear("section", "seccion_ucc");
        const encabezado = utilidades.crear("div", "seccion_encabezado");
        const texto_historial = document.createElement("div");
        texto_historial.append(
            utilidades.crear("h3", "", "Mis informes")
        );
        encabezado.append(texto_historial);
        seccion.append(encabezado);

        if ((datos.informes || []).length === 0) {
            seccion.append(
                utilidades.estado_vacio(
                    "Todavía no ha enviado informes de horas.",
                    "bi-clock-history"
                )
            );
        } else {
            const columnas = [
                {
                    titulo: "Estudiante",
                    valor: "estudiante",
                    clase: "celda_principal"
                },
                { titulo: "Fecha", valor: "fecha_sesion" },
                {
                    titulo: "Horas",
                    valor: function (fila) {
                        return utilidades.texto_horas(fila.cantidad_horas);
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
                    titulo: "Observación",
                    valor: function (fila) {
                        return fila.observacion || "Sin observaciones";
                    },
                    clase: "celda_secundaria"
                },
                { titulo: "Enviado", valor: "fecha_creacion" }
            ];
            seccion.append(
                utilidades.tabla(columnas, datos.informes, "Informes de horas")
            );
        }
        contenedor.append(seccion);
    }

    async function vista_informes(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "monitor_informes",
            contexto,
            function (datos) {
                dibujar_informes(contenedor, datos, contexto);
            }
        );
    }

    window.vistas_ucc.mis_tutorias = vista_mis_tutorias;
    window.vistas_ucc.estudiantes_asignados = vista_asignados;
    window.vistas_ucc.registrar_horas = vista_informes;
})();

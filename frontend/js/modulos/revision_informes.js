window.informes_ucc = (function () {
    const utilidades = window.utilidades_ucc;

    function crear_tarjeta_pendiente(informe, opciones) {
        return utilidades.tarjeta_revision({
            titulo: "Tutoría de " + informe.asignatura,
            subtitulo: "Monitor: " +
                informe.monitor +
                " · Estudiante: " +
                informe.estudiante,
            estado: [informe.estado, informe.estado_texto],
            meta: [
                ["bi-calendar3", informe.fecha_sesion],
                [
                    "bi-clock",
                    informe.hora_inicio + " - " + informe.hora_fin
                ],
                [
                    "bi-hourglass-split",
                    utilidades.texto_horas(informe.cantidad_horas)
                ],
                ["bi-people", informe.estudiantes_atendidos]
            ],
            bloques: [
                { titulo: "Actividades realizadas", texto: informe.actividades }
            ],
            firma: informe.firma_profesor || "",
            campo: {
                id: "observacion_" + informe.id_informe,
                etiqueta: "Observación de revisión",
                placeholder: "Escriba una observación. Es obligatoria si rechaza el informe.",
                ayuda: "La observación quedará registrada en el historial del informe.",
                max: 500
            },
            boton_ok: "Aprobar informe",
            validar: function (texto, decision) {
                if (decision === "rechazar" && !texto) {
                    return "Escriba el motivo antes de rechazar el informe.";
                }
                return null;
            },
            llamar: function (texto, decision) {
                return {
                    accion: opciones.accion,
                    datos: {
                        id_informe: informe.id_informe,
                        decision: decision,
                        observacion: texto
                    }
                };
            },
            ok_msg: "El informe fue revisado.",
            contexto: opciones.contexto,
            despues: function (datos) {
                opciones.al_actualizar(datos);
            }
        });
    }

    function crear_historial(informes, mostrar_profesor) {
        const columnas = [
            {
                titulo: "Monitor",
                valor: "monitor",
                clase: "celda_principal"
            },
            { titulo: "Estudiante", valor: "estudiante" },
            { titulo: "Asignatura", valor: "asignatura" },
            {
                titulo: "Sesión",
                valor: function (informe) {
                    return (
                        informe.fecha_sesion +
                        " · " +
                        informe.hora_inicio +
                        " - " +
                        informe.hora_fin
                    );
                }
            },
            {
                titulo: "Horas",
                valor: function (informe) {
                    return utilidades.texto_horas(informe.cantidad_horas);
                }
            }
        ];

        if (mostrar_profesor) {
            columnas.push({
                titulo: "Profesor",
                valor: function (informe) {
                    return informe.profesor || "Sin registrar";
                }
            });
        }

        columnas.push(
            {
                titulo: "Estado",
                valor: function (informe) {
                    return utilidades.etiqueta_estado(
                        informe.estado,
                        informe.estado_texto
                    );
                }
            },
            {
                titulo: "Observación",
                valor: function (informe) {
                    return informe.observacion || "Sin observaciones";
                },
                clase: "celda_secundaria"
            }
        );

        return utilidades.tabla(
            columnas,
            informes,
            "Historial de informes de horas"
        );
    }

    function dibujar(contenedor, datos, opciones) {
        const pendientes = datos.pendientes || [];
        const historial = datos.historial || [];

        const seccion_pendientes = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_pendientes = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const titulo_pendientes = utilidades.crear(
            "h3",
            "",
            "Informes pendientes"
        );
        const insignia = utilidades.crear(
            "span",
            "insignia_numero",
            pendientes.length
        );
        titulo_pendientes.append(" ", insignia);
        const texto_pendientes = document.createElement("div");
        texto_pendientes.append(
            titulo_pendientes
        );
        encabezado_pendientes.append(texto_pendientes);
        seccion_pendientes.append(encabezado_pendientes);

        if (pendientes.length === 0) {
            seccion_pendientes.append(
                utilidades.estado_vacio(
                    "No hay informes pendientes de revisión.",
                    "bi-check2-all"
                )
            );
        } else {
            pendientes.forEach(function (informe) {
                seccion_pendientes.append(
                    crear_tarjeta_pendiente(informe, opciones)
                );
            });
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
            utilidades.crear("h3", "", "Historial de revisiones")
        );
        encabezado_historial.append(texto_historial);
        seccion_historial.append(encabezado_historial);

        if (historial.length === 0) {
            seccion_historial.append(
                utilidades.estado_vacio(
                    "Aún no hay informes revisados.",
                    "bi-clock-history"
                )
            );
        } else {
            seccion_historial.append(
                crear_historial(
                    historial,
                    Boolean(opciones.mostrar_profesor)
                )
            );
        }

        utilidades.vaciar(contenedor);
        contenedor.append(seccion_pendientes, seccion_historial);
    }

    return {
        dibujar: dibujar
    };
})();

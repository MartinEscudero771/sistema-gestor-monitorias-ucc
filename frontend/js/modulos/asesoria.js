window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    const COLUMNAS_RIESGO = [
        {
            titulo: "Estudiante",
            valor: "nombre",
            clase: "celda_principal"
        },
        { titulo: "Programa", valor: "programa" },
        {
            titulo: "Motivo",
            valor: "motivo",
            clase: "celda_secundaria"
        },
        { titulo: "Monitor", valor: "monitor" },
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
            titulo: "Asignación",
            valor: function (fila) {
                return fila.fecha_asignacion || "Sin asignar";
            }
        }
    ];

    function dibujar_listas(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Listas de riesgo",
                "Consulte los reportes de bajo rendimiento enviados por los profesores.",
                "Gestión de asesoría"
            )
        );

        const listas = datos.listas || [];
        if (listas.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No hay listas de riesgo registradas.",
                    "bi-list-check"
                )
            );
            return;
        }

        contenedor.append(utilidades.acordeon_riesgo({
            id: "listas_asesoria",
            listas: listas,
            contexto: contexto,
            titulo: function (lista) {
                return [lista.asignatura, "Profesor: " + lista.profesor];
            },
            filas: function (lista) {
                return [
                    { etiqueta: "Profesor", valor: lista.profesor },
                    { etiqueta: "Asesor", valor: lista.asesor },
                    { etiqueta: "Enviada", valor: lista.fecha_texto }
                ];
            },
            accion: function (lista) {
                if (!lista.puede_notificar) {
                    return null;
                }
                return {
                    texto: "Recordar a Bienestar",
                    icono: "bi-bell",
                    clase: "boton_claro boton_pequeno",
                    ocupado: "Enviando...",
                    llamar: function (item) {
                        return {
                            accion: "asesoria_notificar_bienestar",
                            datos: { id_lista: item.id_lista }
                        };
                    },
                    ok: "Bienestar recibió el aviso.",
                    despues: function (respuesta) {
                        dibujar_listas(contenedor, respuesta, contexto);
                    }
                };
            },
            columnas: COLUMNAS_RIESGO,
            leyenda: "Estudiantes de la lista de riesgo"
        }));
    }

    async function vista_listas(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "asesoria_listas",
            contexto,
            function (datos) {
                dibujar_listas(contenedor, datos, contexto);
            }
        );
    }

    function crear_tarjeta_asignacion(caso, contexto, contenedor) {
        const tarjeta = utilidades.crear("article", "caso_riesgo");
        const encabezado = utilidades.crear(
            "div",
            "caso_riesgo_encabezado"
        );
        const titulo = document.createElement("div");
        titulo.append(
            utilidades.crear("h4", "", caso.estudiante),
            utilidades.crear(
                "p",
                "",
                caso.programa +
                    " · Promedio " +
                    Number(caso.promedio).toFixed(1) +
                    " · " +
                    caso.materias_reprobadas +
                    " reprobada(s)"
            )
        );
        encabezado.append(titulo, utilidades.etiqueta_estado("pendiente", "Por asignar"));

        const cuerpo = utilidades.crear("div", "caso_riesgo_cuerpo");
        cuerpo.append(
            utilidades.lista_datos([
                { etiqueta: "Asignatura", valor: caso.asignatura },
                { etiqueta: "Profesor", valor: caso.profesor },
                { etiqueta: "Reportado", valor: caso.fecha_texto }
            ])
        );
        const motivo = utilidades.crear("div", "caso_riesgo_motivo");
        motivo.append(
            utilidades.crear("strong", "", "Motivo del reporte"),
            document.createElement("br"),
            document.createTextNode(caso.motivo)
        );
        cuerpo.append(motivo);

        if ((caso.monitores || []).length === 0) {
            cuerpo.append(
                utilidades.alerta(
                    "No hay monitores activos disponibles para esta asignatura.",
                    "alerta",
                    false
                )
            );
            tarjeta.append(encabezado, cuerpo);
            return tarjeta;
        }

        const formulario = document.createElement("form");
        formulario.className = "formulario_ucc";
        const grupo_monitores = utilidades.crear("div", "campo_formulario");
        const grupo = document.createElement("div");
        grupo.setAttribute("role", "radiogroup");
        grupo.setAttribute("aria-label", "Monitor disponible");
        grupo_monitores.append(
            utilidades.crear("p", "form-label", "Monitor disponible")
        );
        caso.monitores.forEach(function (monitor) {
            const opcion = document.createElement("label");
            opcion.className = "monitor_opcion";
            const control = document.createElement("input");
            control.type = "radio";
            control.name = "monitor_" + caso.id_riesgo;
            control.value = monitor.id_monitor;
            control.id =
                "monitor_" + caso.id_riesgo + "_" + monitor.id_monitor;
            const datos_monitor = document.createElement("span");
            datos_monitor.append(
                utilidades.crear("strong", "", monitor.nombre),
                utilidades.crear(
                    "small",
                    "",
                    "Promedio " +
                        Number(monitor.promedio).toFixed(1) +
                        " · " +
                        monitor.programa
                ),
                utilidades.crear(
                    "small",
                    "",
                    monitor.horario_texto
                )
            );
            opcion.append(control, datos_monitor);
            grupo.append(opcion);
        });
        grupo_monitores.append(grupo);

        const observaciones = utilidades.campo({
            id: "observaciones_asignacion_" + caso.id_riesgo,
            etiqueta: "Observaciones de la asignación",
            tipo: "textarea",
            filas: 3,
            maxlength: 500,
            placeholder_texto:
                "Opcional. Indique indicaciones para el monitor o el estudiante."
        });
        const mensaje = utilidades.crear("p", "mensaje_validacion");
        mensaje.hidden = true;
        const acciones = utilidades.crear("div", "acciones_formulario");
        const asignar = utilidades.boton(
            "Asignar monitor",
            "bi-person-check",
            "boton_principal"
        );
        asignar.type = "submit";
        acciones.append(mensaje, asignar);
        formulario.append(
            grupo_monitores,
            observaciones.grupo,
            acciones
        );
        cuerpo.append(formulario);

        formulario.addEventListener("submit", async function (evento) {
            evento.preventDefault();
            mensaje.hidden = true;
            const seleccionado = caso.monitores.find(function (monitor) {
                return document.getElementById(
                    "monitor_" + caso.id_riesgo + "_" + monitor.id_monitor
                ).checked;
            });
            if (!seleccionado) {
                mensaje.textContent =
                    "Seleccione el monitor que realizará el acompañamiento.";
                mensaje.hidden = false;
                grupo.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            utilidades.ocupar_boton(asignar, true, "Asignando...");
            try {
                const respuesta = await window.api_ucc.llamar(
                    "asesoria_asignar_monitor",
                    {
                        id_riesgo: caso.id_riesgo,
                        id_monitor: seleccionado.id_monitor,
                        observaciones:
                            observaciones.control.value.trim()
                    }
                );
                if (!contexto.vigente()) {
                    return;
                }
                utilidades.toast(
                    respuesta.mensaje || "El monitor fue asignado.",
                    "exito"
                );
                dibujar_asignaciones(contenedor, respuesta, contexto);
            } catch (error) {
                if (!contexto.vigente()) {
                    return;
                }
                mensaje.textContent = error.message;
                mensaje.hidden = false;
                utilidades.toast(error.message, "error");
                utilidades.ocupar_boton(asignar, false);
            }
        });

        tarjeta.append(encabezado, cuerpo);
        return tarjeta;
    }

    function dibujar_asignaciones(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Asignar monitor",
                "Relacione cada estudiante en riesgo con un monitor de la misma asignatura.",
                "Acompañamiento académico"
            )
        );

        const pendientes = datos.pendientes || [];
        const resumen = utilidades.crear("div", "alerta_ucc tipo_informacion");
        resumen.append(
            utilidades.icono("bi-info-circle"),
            utilidades.crear(
                "span",
                "alerta_ucc_texto",
                pendientes.length === 1
                    ? "Hay 1 caso pendiente de asignación."
                    : "Hay " +
                          pendientes.length +
                          " casos pendientes de asignación."
            )
        );
        contenedor.append(resumen);

        if (pendientes.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No hay estudiantes pendientes de asignación.",
                    "bi-person-check"
                )
            );
            return;
        }

        const rejilla = utilidades.crear("div", "rejilla_riesgo");
        pendientes.forEach(function (caso) {
            rejilla.append(
                crear_tarjeta_asignacion(caso, contexto, contenedor)
            );
        });
        contenedor.append(rejilla);
    }

    async function vista_asignaciones(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "asesoria_asignacion",
            contexto,
            function (datos) {
                dibujar_asignaciones(contenedor, datos, contexto);
            }
        );
    }

    function dibujar_monitores(contenedor, datos) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Monitores habilitados",
                "Consulte cobertura, horarios y carga académica de los monitores activos.",
                "Directorio de monitores"
            )
        );

        const monitores = datos.monitores || [];
        if (monitores.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No hay monitores activos en este momento.",
                    "bi-people"
                )
            );
            return;
        }

        const columnas = [
            {
                titulo: "Monitor",
                valor: "nombre",
                clase: "celda_principal"
            },
            { titulo: "Programa", valor: "programa" },
            { titulo: "Asignatura", valor: "asignatura" },
            {
                titulo: "Promedio",
                valor: function (fila) {
                    return Number(fila.promedio).toFixed(1);
                }
            },
            {
                titulo: "Máx. horas semanales",
                valor: "max_horas_semanales"
            },
            { titulo: "Asignados", valor: "total_asignados" },
            {
                titulo: "Horas aprobadas",
                valor: function (fila) {
                    return utilidades.texto_horas(fila.total_horas);
                }
            },
            {
                titulo: "Horario",
                valor: "horario_texto",
                clase: "celda_secundaria"
            }
        ];
        contenedor.append(
            utilidades.tabla(columnas, monitores, "Monitores habilitados")
        );
    }

    async function vista_monitores(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "asesoria_monitores",
            contexto,
            function (datos) {
                dibujar_monitores(contenedor, datos);
            }
        );
    }

    function crear_tarjeta_solicitud(solicitud, contexto, contenedor) {
        return utilidades.tarjeta_revision({
            titulo: solicitud.estudiante,
            subtitulo: solicitud.programa +
                " · " +
                solicitud.asignatura +
                " · Solicitada " +
                solicitud.fecha_texto,
            estado: [solicitud.estado, solicitud.estado_texto],
            meta: [
                ["bi-calendar3", solicitud.fecha_preferida],
                ["bi-clock", solicitud.hora_preferida],
                ["bi-book", solicitud.asignatura]
            ],
            bloques: [
                { titulo: "Tema solicitado", texto: solicitud.tema }
            ],
            campo: {
                id: "respuesta_solicitud_" + solicitud.id_solicitud,
                etiqueta: "Respuesta para el estudiante",
                placeholder: "Explique la respuesta o las indicaciones para el estudiante.",
                ayuda: "Entre 5 y 500 caracteres. Es obligatoria."
            },
            boton_ok: "Aceptar solicitud",
            validar: function (texto) {
                if (texto.length < 5) {
                    return "Escriba una respuesta de al menos 5 caracteres.";
                }
                return null;
            },
            llamar: function (texto, decision) {
                return {
                    accion: "asesoria_responder_solicitud",
                    datos: {
                        id_solicitud: solicitud.id_solicitud,
                        decision: decision,
                        respuesta: texto
                    }
                };
            },
            ok_msg: "La solicitud fue respondida.",
            contexto: contexto,
            despues: function (datos) {
                dibujar_solicitudes(contenedor, datos, contexto);
            }
        });
    }

    function dibujar_solicitudes(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Solicitudes de monitoría",
                "Responda las solicitudes de apoyo enviadas por los estudiantes.",
                "Atención estudiantil"
            )
        );

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
        const texto_pendientes = document.createElement("div");
        const titulo_pendientes = utilidades.crear(
            "h3",
            "",
            "Solicitudes pendientes"
        );
        titulo_pendientes.append(
            " ",
            utilidades.crear(
                "span",
                "insignia_numero",
                pendientes.length
            )
        );
        texto_pendientes.append(
            titulo_pendientes
        );
        encabezado_pendientes.append(texto_pendientes);
        seccion_pendientes.append(encabezado_pendientes);

        if (pendientes.length === 0) {
            seccion_pendientes.append(
                utilidades.estado_vacio(
                    "No hay solicitudes pendientes de respuesta.",
                    "bi-chat-check"
                )
            );
        } else {
            pendientes.forEach(function (solicitud) {
                seccion_pendientes.append(
                    crear_tarjeta_solicitud(
                        solicitud,
                        contexto,
                        contenedor
                    )
                );
            });
        }
        contenedor.append(seccion_pendientes);

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
            utilidades.crear("h3", "", "Historial de solicitudes")
        );
        encabezado_historial.append(texto_historial);
        seccion_historial.append(encabezado_historial);

        if (historial.length === 0) {
            seccion_historial.append(
                utilidades.estado_vacio(
                    "Aún no hay solicitudes respondidas.",
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
                { titulo: "Asignatura", valor: "asignatura" },
                {
                    titulo: "Tema",
                    valor: "tema",
                    clase: "celda_secundaria"
                },
                {
                    titulo: "Sesión preferida",
                    valor: function (fila) {
                        return (
                            fila.fecha_preferida +
                            " · " +
                            fila.hora_preferida
                        );
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
                    valor: "respuesta",
                    clase: "celda_secundaria"
                }
            ];
            seccion_historial.append(
                utilidades.tabla(
                    columnas,
                    historial,
                    "Historial de solicitudes"
                )
            );
        }
        contenedor.append(seccion_historial);
    }

    async function vista_solicitudes(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "asesoria_solicitudes",
            contexto,
            function (datos) {
                dibujar_solicitudes(contenedor, datos, contexto);
            }
        );
    }

    window.vistas_ucc.listas_riesgo = vista_listas;
    window.vistas_ucc.asignar_monitor = vista_asignaciones;
    window.vistas_ucc.monitores = vista_monitores;
    window.vistas_ucc.solicitudes = vista_solicitudes;
})();

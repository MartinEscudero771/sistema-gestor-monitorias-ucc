window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    function crear_formulario_curso(curso, contexto, contenedor, datos) {
        const panel = utilidades.crear("section", "panel_ucc");
        const encabezado = utilidades.crear(
            "div",
            "panel_ucc_encabezado"
        );
        const informacion = document.createElement("div");
        informacion.append(
            utilidades.crear("h3", "", curso.nombre),
            utilidades.crear(
                "p",
                "",
                "Código " +
                    curso.codigo +
                    " · Periodo " +
                    curso.periodo
            )
        );
        encabezado.append(informacion);

        const cuerpo = utilidades.crear("div", "panel_ucc_cuerpo");
        const formulario = document.createElement("form");
        formulario.className = "formulario_ucc";

        const lista = utilidades.crear(
            "div",
            "lista_seleccion_estudiantes"
        );
        const controles = [];
        let disponibles = 0;

        curso.estudiantes.forEach(function (estudiante) {
            const disponible =
                estudiante.bajo_rendimiento && !estudiante.en_lista_activa;
            const opcion = document.createElement("label");
            opcion.className =
                "opcion_estudiante" + (disponible ? "" : " bloqueada");
            const casilla = document.createElement("input");
            casilla.type = "checkbox";
            casilla.className = "form-check-input";
            casilla.id =
                "riesgo_" + curso.id_curso + "_" + estudiante.id_estudiante;
            casilla.value = estudiante.id_estudiante;
            casilla.disabled = !disponible;
            casilla.setAttribute(
                "aria-label",
                "Seleccionar a " + estudiante.nombre
            );
            if (disponible) {
                disponibles += 1;
                controles.push(casilla);
            }

            const datos_estudiante = utilidades.crear(
                "span",
                "opcion_estudiante_datos"
            );
            datos_estudiante.append(
                utilidades.crear("strong", "", estudiante.nombre),
                utilidades.crear(
                    "small",
                    "",
                    estudiante.programa +
                        " · Promedio " +
                        Number(estudiante.promedio).toFixed(1) +
                        " · Nota " +
                        Number(estudiante.nota_final).toFixed(1)
                )
            );

            let indicador;
            if (estudiante.en_lista_activa) {
                indicador = utilidades.etiqueta_neutra(
                    "En lista activa"
                );
            } else if (estudiante.bajo_rendimiento) {
                indicador = utilidades.crear(
                    "span",
                    "indicador_criterio",
                    estudiante.materias_reprobadas +
                        " reprobada(s)"
                );
                indicador.prepend(
                    utilidades.icono("bi-exclamation-triangle")
                );
            } else {
                indicador = utilidades.crear(
                    "span",
                    "indicador_criterio ok",
                    "Sin criterio de riesgo"
                );
                indicador.prepend(utilidades.icono("bi-check2"));
            }

            opcion.append(casilla, datos_estudiante, indicador);
            lista.append(opcion);
        });

        const campo_observaciones = utilidades.campo({
            id: "observaciones_" + curso.id_curso,
            etiqueta: "Observaciones para Asesoría",
            tipo: "textarea",
            filas: 3,
            maxlength: 500,
            placeholder_texto:
                "Opcional. Describa la situación general del grupo o indicaciones de acompañamiento.",
            ancho: true
        });

        const mensaje = utilidades.crear("p", "mensaje_validacion");
        mensaje.hidden = true;
        const acciones = utilidades.crear("div", "acciones_formulario");
        const enviar = utilidades.boton(
            "Enviar lista de riesgo",
            "bi-send",
            "boton_principal"
        );
        enviar.type = "submit";
        enviar.disabled = disponibles === 0;
        acciones.append(mensaje, enviar);

        formulario.append(lista, campo_observaciones.grupo, acciones);
        cuerpo.append(formulario);
        if (disponibles === 0) {
            cuerpo.prepend(
                utilidades.alerta(
                    "No hay estudiantes disponibles para reportar en este curso: deben tener bajo rendimiento y no pertenecer a una lista activa.",
                    "informacion"
                )
            );
        } else {
            cuerpo.prepend(
                utilidades.crear(
                    "p",
                    "campo_ayuda",
                    disponibles +
                        " estudiante(s) pueden incluirse en una nueva lista."
                )
            );
        }
        panel.append(encabezado, cuerpo);

        formulario.addEventListener("submit", async function (evento) {
            evento.preventDefault();
            mensaje.hidden = true;
            const seleccionados = controles
                .filter(function (control) {
                    return control.checked;
                })
                .map(function (control) {
                    return control.value;
                });

            if (seleccionados.length === 0) {
                mensaje.textContent =
                    "Seleccione al menos un estudiante para enviar la lista.";
                mensaje.hidden = false;
                return;
            }

            utilidades.ocupar_boton(enviar, true, "Enviando...");
            try {
                const respuesta = await window.api_ucc.llamar(
                    "profesor_guardar_lista",
                    {
                        id_curso: curso.id_curso,
                        ids_estudiantes: seleccionados,
                        observaciones:
                            campo_observaciones.control.value.trim()
                    }
                );
                if (!contexto.vigente()) {
                    return;
                }
                utilidades.toast(
                    respuesta.mensaje || "La lista fue enviada.",
                    "exito"
                );
                dibujar_riesgo(contenedor, respuesta, contexto);
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

        return panel;
    }

    function dibujar_riesgo(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Estudiantes en riesgo",
                "Seleccione los estudiantes con bajo rendimiento que requieren acompañamiento. La lista será enviada a Asesoría.",
                "Seguimiento académico"
            )
        );

        const cursos = datos.cursos || [];
        if (cursos.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No tiene cursos asignados actualmente.",
                    "bi-journal-x"
                )
            );
            return;
        }

        cursos.forEach(function (curso) {
            contenedor.append(
                crear_formulario_curso(curso, contexto, contenedor, datos)
            );
        });

        const seccion_recientes = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_recientes = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_recientes = document.createElement("div");
        texto_recientes.append(
            utilidades.crear("h3", "", "Últimas listas enviadas")
        );
        encabezado_recientes.append(texto_recientes);
        seccion_recientes.append(encabezado_recientes);

        const recientes = datos.listas_recientes || [];
        if (recientes.length === 0) {
            seccion_recientes.append(
                utilidades.estado_vacio(
                    "Todavía no ha enviado listas de riesgo.",
                    "bi-list-check"
                )
            );
        } else {
            const columnas = [
                {
                    titulo: "Curso",
                    valor: "curso",
                    clase: "celda_principal"
                },
                { titulo: "Enviada", valor: "fecha_texto" },
                {
                    titulo: "Estudiantes",
                    valor: function (fila) {
                        return (fila.estudiantes || []).length;
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
                { titulo: "Asesor", valor: "asesor" }
            ];
            seccion_recientes.append(
                utilidades.tabla(
                    columnas,
                    recientes,
                    "Últimas listas de riesgo"
                )
            );
        }
        contenedor.append(seccion_recientes);
    }

    async function vista_riesgo(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "profesor_riesgo",
            contexto,
            function (datos) {
                dibujar_riesgo(contenedor, datos, contexto);
            }
        );
    }

    const COLUMNAS_LISTA = [
        {
            titulo: "Estudiante",
            valor: "nombre",
            clase: "celda_principal"
        },
        {
            titulo: "Programa",
            valor: "programa",
            clase: "celda_secundaria"
        },
        {
            titulo: "Motivo",
            valor: "motivo",
            clase: "celda_secundaria"
        },
        {
            titulo: "Monitor",
            valor: "monitor"
        },
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

    function dibujar_listas(contenedor, datos) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Mis listas de riesgo",
                "Consulte el estado de los reportes enviados y el monitor asignado a cada estudiante.",
                "Historial de reportes"
            )
        );

        const listas = datos.listas || [];
        if (listas.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "Todavía no ha enviado listas de riesgo.",
                    "bi-list-check"
                )
            );
            return;
        }

        contenedor.append(utilidades.acordeon_riesgo({
            id: "listas_riesgo",
            listas: listas,
            titulo: function (lista) {
                return [lista.curso, lista.fecha_texto];
            },
            filas: function (lista) {
                return [
                    { etiqueta: "Asignatura", valor: lista.asignatura },
                    { etiqueta: "Asesor", valor: lista.asesor },
                    { etiqueta: "Enviada", valor: lista.fecha_texto },
                    {
                        etiqueta: "Observaciones",
                        valor: lista.observaciones || "Sin observaciones"
                    }
                ];
            },
            columnas: COLUMNAS_LISTA,
            leyenda: "Estudiantes de la lista"
        }));
    }

    async function vista_listas(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "profesor_listas",
            contexto,
            function (datos) {
                dibujar_listas(contenedor, datos);
            }
        );
    }

    function dibujar_horas(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Validar horas",
                "Revise los informes enviados por los monitores y apruébelos o rechácelos con una observación.",
                "Revisión de informes"
            )
        );
        const cuerpo = utilidades.crear("div", "contenido_apilado");
        contenedor.append(cuerpo);
        window.informes_ucc.dibujar(cuerpo, datos, {
            accion: "profesor_decidir_informe",
            contexto: contexto,
            mostrar_profesor: false,
            al_actualizar: function (nuevos_datos) {
                dibujar_horas(contenedor, nuevos_datos, contexto);
            }
        });
    }

    async function vista_horas(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "profesor_informes",
            contexto,
            function (datos) {
                dibujar_horas(contenedor, datos, contexto);
            }
        );
    }

    window.vistas_ucc.estudiantes_riesgo = vista_riesgo;
    window.vistas_ucc.mis_listas = vista_listas;
    window.vistas_ucc.validar_horas_profesor = vista_horas;
})();

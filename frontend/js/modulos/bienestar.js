window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    function crear_tarjeta_postulacion(postulacion, contexto, contenedor) {
        return utilidades.tarjeta_revision({
            titulo: postulacion.estudiante,
            subtitulo: postulacion.programa +
                " · Semestre " +
                postulacion.semestre +
                " · " +
                postulacion.correo,
            estado: [
                postulacion.elegible ? "pendiente" : "rechazada",
                postulacion.elegible ? "Elegible" : "Revisar requisitos"
            ],
            meta: [
                [
                    "bi-graph-up-arrow",
                    "Promedio " + Number(postulacion.promedio).toFixed(1)
                ],
                [
                    "bi-journal-x",
                    postulacion.materias_reprobadas +
                        " materia(s) reprobada(s)"
                ],
                ["bi-book", postulacion.asignatura],
                ["bi-calendar3", postulacion.fecha_texto]
            ],
            bloques: [
                {
                    titulo: "Disponibilidad registrada",
                    texto: postulacion.horario_texto,
                    clase: "bloque_texto"
                }
            ],
            alertas: (postulacion.motivos || []).length > 0
                ? [postulacion.motivos.join(" ")]
                : [],
            campo: {
                id: "motivo_postulacion_" + postulacion.id_postulacion,
                etiqueta: "Motivo u observación",
                placeholder: "Escriba una observación. Es obligatoria si rechaza la postulación.",
                max: 400
            },
            boton_ok: "Aprobar monitor",
            icono_ok: "bi-person-check",
            ok_deshabilitado: !postulacion.elegible,
            validar: function (texto, decision) {
                if (decision === "rechazar" && !texto) {
                    return "Escriba el motivo antes de rechazar la postulación.";
                }
                return null;
            },
            llamar: function (texto, decision) {
                return {
                    accion: "bienestar_decidir_postulacion",
                    datos: {
                        id_postulacion: postulacion.id_postulacion,
                        decision: decision,
                        motivo: texto
                    }
                };
            },
            ok_msg: "La postulación fue revisada.",
            contexto: contexto,
            despues: function (respuesta) {
                dibujar_monitores(contenedor, respuesta, contexto);
            }
        });
    }

    function dibujar_monitores(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Validar monitores",
                "Revise las postulaciones estudiantiles y consulte los monitores habilitados.",
                "Bienestar Universitario"
            )
        );

        const postulaciones = datos.postulaciones || [];
        const monitores = datos.monitores_activos || [];
        const rejilla = utilidades.crear("div", "rejilla_metricas");
        rejilla.append(
            utilidades.tarjeta_metrica({
                titulo: "Postulaciones pendientes",
                valor: postulaciones.length,
                detalle: "Por revisar",
                icono: "bi-person-plus",
                tipo: postulaciones.length > 0 ? "amarillo" : "verde"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Monitores activos",
                valor: monitores.length,
                detalle: "Habilitados en el sistema",
                icono: "bi-person-badge",
                tipo: "verde"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Asignaturas cubiertas",
                valor: new Set(
                    monitores.map(function (item) {
                        return item.asignatura;
                    })
                ).size,
                detalle: "Con acompañamiento disponible",
                icono: "bi-book",
                tipo: "azul"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Estudiantes asignados",
                valor: monitores.reduce(function (total, item) {
                    return total + Number(item.total_asignados || 0);
                }, 0),
                detalle: "Acompañamientos activos",
                icono: "bi-people",
                tipo: "gris"
            })
        );
        contenedor.append(rejilla);

        const seccion_postulaciones = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_postulaciones = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_postulaciones = document.createElement("div");
        const titulo_postulaciones = utilidades.crear(
            "h3",
            "",
            "Postulaciones pendientes"
        );
        titulo_postulaciones.append(
            " ",
            utilidades.crear(
                "span",
                "insignia_numero",
                postulaciones.length
            )
        );
        texto_postulaciones.append(
            titulo_postulaciones
        );
        encabezado_postulaciones.append(texto_postulaciones);
        seccion_postulaciones.append(encabezado_postulaciones);

        if (postulaciones.length === 0) {
            seccion_postulaciones.append(
                utilidades.estado_vacio(
                    "No hay postulaciones pendientes de revisión.",
                    "bi-person-check"
                )
            );
        } else {
            postulaciones.forEach(function (postulacion) {
                seccion_postulaciones.append(
                    crear_tarjeta_postulacion(
                        postulacion,
                        contexto,
                        contenedor
                    )
                );
            });
        }
        contenedor.append(seccion_postulaciones);

        const seccion_monitores = utilidades.crear(
            "section",
            "seccion_ucc"
        );
        const encabezado_monitores = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        const texto_monitores = document.createElement("div");
        texto_monitores.append(
            utilidades.crear("h3", "", "Monitores activos")
        );
        encabezado_monitores.append(texto_monitores);
        seccion_monitores.append(encabezado_monitores);

        if (monitores.length === 0) {
            seccion_monitores.append(
                utilidades.estado_vacio(
                    "No hay monitores activos en este momento.",
                    "bi-people"
                )
            );
        } else {
            const columnas = [
                {
                    titulo: "Monitor",
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
                                fila.correo
                            )
                        );
                        return contenedor_nombre;
                    }
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
                    titulo: "Máx. horas",
                    valor: "max_horas_semanales"
                },
                { titulo: "Asignados", valor: "total_asignados" },
                { titulo: "Activado", valor: "fecha_activacion" }
            ];
            seccion_monitores.append(
                utilidades.tabla(
                    columnas,
                    monitores,
                    "Monitores habilitados"
                )
            );
        }
        contenedor.append(seccion_monitores);
    }

    async function vista_monitores(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "bienestar_monitores",
            contexto,
            function (datos) {
                dibujar_monitores(contenedor, datos, contexto);
            }
        );
    }

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

    function dibujar_riesgo(contenedor, datos) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Gestión de riesgo",
                "Supervise las listas de bajo rendimiento y el estado del acompañamiento.",
                "Seguimiento institucional"
            )
        );

        const listas = datos.listas || [];
        if (listas.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No hay listas de riesgo registradas.",
                    "bi-shield-check"
                )
            );
            return;
        }

        contenedor.append(utilidades.acordeon_riesgo({
            id: "riesgo_bienestar",
            listas: listas,
            titulo: function (lista) {
                return [lista.asignatura, "Profesor: " + lista.profesor];
            },
            filas: function (lista) {
                return [
                    { etiqueta: "Profesor", valor: lista.profesor },
                    { etiqueta: "Asesor", valor: lista.asesor },
                    { etiqueta: "Enviada", valor: lista.fecha_texto },
                    {
                        etiqueta: "Estado",
                        valor: utilidades.etiqueta_estado(
                            lista.estado,
                            lista.estado_texto
                        )
                    }
                ];
            },
            columnas: COLUMNAS_RIESGO,
            leyenda: "Estudiantes en riesgo"
        }));
    }

    async function vista_riesgo(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "bienestar_riesgo",
            contexto,
            function (datos) {
                dibujar_riesgo(contenedor, datos);
            }
        );
    }

    function dibujar_horas(contenedor, datos, contexto) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Aprobar horas",
                "Realice la revisión final de los informes que ya cuentan con la aprobación del profesor.",
                "Validación final"
            )
        );
        const cuerpo = utilidades.crear("div", "contenido_apilado");
        contenedor.append(cuerpo);
        window.informes_ucc.dibujar(cuerpo, datos, {
            accion: "bienestar_decidir_informe",
            contexto: contexto,
            mostrar_profesor: true,
            al_actualizar: function (nuevos_datos) {
                dibujar_horas(contenedor, nuevos_datos, contexto);
            }
        });
    }

    async function vista_horas(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "bienestar_informes",
            contexto,
            function (datos) {
                dibujar_horas(contenedor, datos, contexto);
            }
        );
    }

    window.vistas_ucc.validar_monitores = vista_monitores;
    window.vistas_ucc.riesgo = vista_riesgo;
    window.vistas_ucc.validar_horas_bienestar = vista_horas;
})();

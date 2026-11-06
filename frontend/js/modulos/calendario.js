window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;
    let instancia_calendario = null;

    function contar_eventos(eventos, estado) {
        return eventos.filter(function (evento) {
            return evento.estado === estado;
        }).length;
    }

    function crear_resumen(eventos) {
        const resumen = utilidades.crear("div", "resumen_calendario");
        const datos = [
            {
                valor: contar_eventos(eventos, "programada"),
                etiqueta: "Programadas"
            },
            {
                valor: contar_eventos(eventos, "realizada"),
                etiqueta: "Realizadas"
            },
            {
                valor: contar_eventos(eventos, "cancelada"),
                etiqueta: "Canceladas"
            }
        ];
        datos.forEach(function (dato) {
            const elemento = utilidades.crear(
                "div",
                "resumen_calendario_item"
            );
            elemento.append(
                utilidades.crear("strong", "", dato.valor),
                utilidades.crear("span", "", dato.etiqueta)
            );
            resumen.append(elemento);
        });
        return resumen;
    }

    function mostrar_detalle(contenedor, evento) {
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.crear("p", "etiqueta_superior", "Detalle de la sesión"),
            utilidades.crear("h3", "", evento.titulo)
        );
        const estado = utilidades.etiqueta_estado(
            evento.estado,
            evento.estado_texto
        );
        contenedor.append(estado);

        const datos = [
            { etiqueta: "Fecha", valor: evento.fecha_texto },
            { etiqueta: "Horario", valor: evento.hora_texto },
            { etiqueta: "Modalidad", valor: evento.modalidad },
            { etiqueta: "Lugar o enlace", valor: evento.lugar },
            { etiqueta: "Monitor", valor: evento.monitor },
            { etiqueta: "Estudiante", valor: evento.estudiante },
            { etiqueta: "Profesor", valor: evento.profesor }
        ];
        const lista = utilidades.lista_datos(datos);
        lista.style.marginTop = "14px";
        contenedor.append(lista);
    }

    function crear_lista_eventos(eventos, detalle) {
        const lista = utilidades.crear("div", "lista_eventos");
        if (eventos.length === 0) {
            lista.append(
                utilidades.estado_vacio(
                    "No hay tutorías registradas en el calendario.",
                    "bi-calendar-x",
                    true
                )
            );
            return lista;
        }

        eventos.forEach(function (evento) {
            const elemento = utilidades.crear("button", "boton_evento");
            elemento.type = "button";
            const color = utilidades.crear(
                "span",
                "boton_evento_color"
            );
            color.style.background = evento.color;
            const contenido = document.createElement("span");
            contenido.append(
                utilidades.crear("strong", "", evento.titulo),
                utilidades.crear(
                    "small",
                    "",
                    evento.fecha_texto + " · " + evento.hora_texto
                ),
                utilidades.crear(
                    "small",
                    "",
                    evento.estado_texto + " · " + evento.modalidad
                )
            );
            elemento.append(color, contenido);
            elemento.addEventListener("click", function () {
                mostrar_detalle(detalle, evento);
                detalle.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest"
                });
            });
            lista.append(elemento);
        });
        return lista;
    }

    function dibujar(contenedor, datos) {
        utilidades.vaciar(contenedor);
        const eventos = datos.eventos || [];

        contenedor.append(
            utilidades.encabezado(
                "Calendario de tutorías",
                "Consulte las sesiones programadas, realizadas y canceladas de su proceso académico.",
                "Agenda académica"
            )
        );

        if (eventos.length === 0) {
            contenedor.append(
                utilidades.estado_vacio(
                    "Todavía no hay tutorías para mostrar en el calendario.",
                    "bi-calendar3"
                )
            );
            return;
        }

        const distribucion = utilidades.crear("div", "calendario_layout");
        const marco = utilidades.crear("div", "calendario_marco");
        const contenedor_calendario = document.createElement("div");
        contenedor_calendario.id = "calendario_academico";
        marco.append(contenedor_calendario);

        const lateral = utilidades.crear("aside", "panel_calendario_lateral");
        const panel_detalle = utilidades.crear(
            "div",
            "detalle_calendario"
        );
        mostrar_detalle(panel_detalle, eventos[0]);

        const panel_lista = utilidades.crear(
            "div",
            "tarjeta_detalle"
        );
        panel_lista.style.marginTop = "12px";
        panel_lista.append(
            utilidades.crear("h4", "", "Todas las sesiones")
        );
        const lista = crear_lista_eventos(eventos, panel_detalle);
        lista.style.marginTop = "10px";
        panel_lista.append(crear_resumen(eventos), lista);

        lateral.append(panel_detalle, panel_lista);
        distribucion.append(marco, lateral);
        contenedor.append(distribucion);

        if (instancia_calendario) {
            instancia_calendario.destroy();
            instancia_calendario = null;
        }

        if (
            typeof FullCalendar === "undefined" ||
            !FullCalendar.Calendar
        ) {
            contenedor_calendario.append(
                utilidades.alerta(
                    "No fue posible cargar el componente del calendario.",
                    "alerta"
                )
            );
            return;
        }

        const eventos_calendario = eventos.map(function (evento) {
            return {
                id: evento.id_evento,
                title: evento.titulo,
                start: evento.inicio,
                end: evento.fin,
                backgroundColor: evento.color,
                borderColor: evento.color,
                textColor: "#ffffff",
                extendedProps: {
                    datos_evento: evento
                }
            };
        });

        instancia_calendario = new FullCalendar.Calendar(
            contenedor_calendario,
            {
                initialView: "dayGridMonth",
                locale: "es",
                firstDay: 1,
                height: "auto",
                headerToolbar: {
                    left: "prev,next today",
                    center: "title",
                    right: "dayGridMonth,timeGridWeek"
                },
                buttonText: {
                    today: "Hoy",
                    month: "Mes",
                    week: "Semana"
                },
                dayMaxEvents: 3,
                eventDisplay: "block",
                eventTimeFormat: {
                    hour: "numeric",
                    minute: "2-digit",
                    meridiem: "short"
                },
                slotMinTime: "06:00:00",
                slotMaxTime: "22:00:00",
                allDaySlot: false,
                noEventsText: "No hay tutorías en este periodo.",
                events: eventos_calendario,
                eventClick: function (informacion) {
                    mostrar_detalle(
                        panel_detalle,
                        informacion.event.extendedProps.datos_evento
                    );
                    informacion.jsEvent.preventDefault();
                }
            }
        );
        instancia_calendario.render();
    }

    async function vista_calendario(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "calendario_listar",
            contexto,
            function (datos) {
                dibujar(contenedor, datos);
            }
        );
    }

    window.vistas_ucc.calendario = vista_calendario;
})();

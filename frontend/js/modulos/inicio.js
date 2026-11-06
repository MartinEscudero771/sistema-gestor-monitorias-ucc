window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;

    function icono_actividad(tipo) {
        return utilidades.icono_alerta(tipo);
    }

    function icono_rol() {
        if (!window.app_ucc || !window.app_ucc.obtener_usuario()) {
            return "bi-mortarboard";
        }
        const rol = window.app_ucc.obtener_usuario().rol;
        const iconos = {
            estudiante: "bi-mortarboard",
            monitor: "bi-person-workspace",
            profesor: "bi-person-video3",
            bienestar: "bi-heart-pulse",
            asesoria: "bi-compass",
            admin: "bi-shield-check"
        };
        return iconos[rol] || "bi-mortarboard";
    }

    function dibujar_panel(contenedor, panel) {
        utilidades.vaciar(contenedor);
        if (!panel) {
            contenedor.append(
                utilidades.estado_vacio(
                    "No fue posible cargar el resumen del panel.",
                    "bi-grid",
                    false
                )
            );
            return;
        }

        const portada = utilidades.crear("section", "portada_panel");
        const contenido = utilidades.crear("div", "portada_panel_contenido");
        const usuario =
            window.app_ucc && window.app_ucc.obtener_usuario()
                ? window.app_ucc.obtener_usuario()
                : null;
        contenido.append(
            utilidades.crear(
                "p",
                "portada_panel_etiqueta",
                usuario ? usuario.rol_texto : "Panel académico"
            ),
            utilidades.crear("h2", "", panel.titulo || "Panel de inicio")
        );
        const caja_icono = utilidades.crear("div", "portada_panel_icono");
        caja_icono.append(utilidades.icono(icono_rol()));
        portada.append(contenido, caja_icono);

        const metricas = utilidades.crear("section", "rejilla_metricas");
        (panel.tarjetas || []).forEach(function (tarjeta) {
            metricas.append(utilidades.tarjeta_metrica(tarjeta));
        });

        const rejilla = utilidades.crear("div", "rejilla_principal");
        const columna_actividad = utilidades.crear("section", "seccion_ucc");
        const encabezado_actividad = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        encabezado_actividad.append(
            utilidades.crear("h3", "", "Actividad reciente")
        );

        const lista_actividad = utilidades.crear("div", "panel_lista");
        if (!panel.actividad || panel.actividad.length === 0) {
            lista_actividad.append(
                utilidades.estado_vacio(
                    "Todavía no hay movimientos recientes.",
                    "bi-activity",
                    true
                )
            );
        } else {
            panel.actividad.forEach(function (actividad) {
                const elemento = utilidades.crear(
                    "article",
                    "elemento_actividad"
                );
                const caja = utilidades.crear(
                    "div",
                    "elemento_actividad_icono tipo_" +
                        (actividad.tipo || "informacion")
                );
                caja.append(utilidades.icono(icono_actividad(actividad.tipo)));
                const datos = utilidades.crear("div", "");
                datos.append(
                    utilidades.crear("strong", "", actividad.titulo),
                    utilidades.crear("p", "", actividad.detalle),
                    utilidades.crear("small", "", actividad.fecha)
                );
                elemento.append(caja, datos);
                lista_actividad.append(elemento);
            });
        }
        columna_actividad.append(encabezado_actividad, lista_actividad);

        const columna_alertas = utilidades.crear("section", "seccion_ucc");
        const encabezado_alertas = utilidades.crear(
            "div",
            "seccion_encabezado"
        );
        encabezado_alertas.append(
            utilidades.crear("h3", "", "Alertas y avisos")
        );

        let contenido_alertas;
        if (!panel.alertas || panel.alertas.length === 0) {
            contenido_alertas = utilidades.estado_vacio(
                "No tiene alertas pendientes. Su información está al día.",
                "bi-shield-check",
                true
            );
        } else {
            contenido_alertas = utilidades.lista_alertas(panel.alertas);
        }
        columna_alertas.append(encabezado_alertas, contenido_alertas);

        rejilla.append(columna_actividad, columna_alertas);
        contenedor.append(portada);
        if ((panel.tarjetas || []).length > 0) {
            contenedor.append(metricas);
        }
        contenedor.append(rejilla);
    }

    async function vista_inicio(contenedor, contexto) {
        await utilidades.cargar_vista(
            contenedor,
            "panel_inicio",
            contexto,
            function (datos) {
                dibujar_panel(contenedor, datos);
            }
        );
    }

    vista_inicio.dibujar_panel = dibujar_panel;
    window.vistas_ucc.inicio = vista_inicio;
})();

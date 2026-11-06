window.notificaciones_ucc = (function () {
    const utilidades = window.utilidades_ucc;
    let iniciado = false;
    let cargando = false;
    let generacion_sesion = 0;

    function icono_por_tipo(tipo) {
        return utilidades.icono_alerta(tipo);
    }

    function actualizar_contador(numero) {
        const contador = document.getElementById("contador_notificaciones");
        if (!contador) {
            return;
        }
        const cantidad = Number(numero) || 0;
        if (cantidad > 0) {
            contador.textContent = cantidad > 99 ? "99+" : String(cantidad);
            contador.classList.remove("d-none");
            contador.setAttribute(
                "aria-label",
                cantidad + " notificaciones sin leer"
            );
        } else {
            contador.textContent = "0";
            contador.classList.add("d-none");
            contador.removeAttribute("aria-label");
        }
    }

    function crear_elemento_notificacion(notificacion) {
        const elemento = document.createElement(
            notificacion.leida ? "div" : "button"
        );
        elemento.className =
            "notificacion" +
            (notificacion.leida ? "" : " notificacion_no_leida");
        if (!notificacion.leida) {
            elemento.type = "button";
            elemento.setAttribute(
                "aria-label",
                "Marcar como leída: " + notificacion.titulo
            );
        }

        const caja_icono = utilidades.crear(
            "div",
            "notificacion_icono tipo_" + (notificacion.tipo || "informacion")
        );
        caja_icono.append(utilidades.icono(icono_por_tipo(notificacion.tipo)));

        const contenido = utilidades.crear("div", "notificacion_contenido");
        contenido.append(
            utilidades.crear("strong", "", notificacion.titulo),
            utilidades.crear("p", "", notificacion.mensaje),
            utilidades.crear("small", "", notificacion.fecha_texto)
        );

        elemento.append(caja_icono, contenido);

        if (!notificacion.leida) {
            const punto = utilidades.crear("span", "punto_notificacion");
            punto.setAttribute("aria-hidden", "true");
            elemento.append(punto);
            elemento.addEventListener("click", function () {
                marcar_leida(notificacion.id_notificacion, elemento);
            });
        } else {
            const marca = utilidades.crear(
                "span",
                "etiqueta_neutra",
                "Leída"
            );
            elemento.append(marca);
        }

        return elemento;
    }

    function dibujar(datos) {
        const lista = document.getElementById("lista_notificaciones");
        const resumen = document.getElementById("resumen_notificaciones");
        const boton_todas = document.getElementById("boton_marcar_todas");
        if (!lista || !resumen || !boton_todas) {
            return;
        }

        const notificaciones = datos.notificaciones || [];
        const no_leidas =
            typeof datos.no_leidas === "number"
                ? datos.no_leidas
                : notificaciones.filter(function (item) {
                      return !item.leida;
                  }).length;

        utilidades.vaciar(lista);
        if (notificaciones.length === 0) {
            lista.append(
                utilidades.estado_vacio(
                    "No tiene notificaciones por el momento.",
                    "bi-bell-slash",
                    true
                )
            );
        } else {
            notificaciones.forEach(function (notificacion) {
                lista.append(crear_elemento_notificacion(notificacion));
            });
        }

        resumen.textContent =
            no_leidas === 0
                ? "Está al día con sus notificaciones."
                : no_leidas === 1
                  ? "1 notificación sin leer."
                  : no_leidas + " notificaciones sin leer.";
        boton_todas.disabled = no_leidas === 0;

        actualizar_contador(no_leidas);
    }

    async function cargar() {
        if (cargando) {
            return;
        }
        const lista = document.getElementById("lista_notificaciones");
        const resumen = document.getElementById("resumen_notificaciones");
        const boton_todas = document.getElementById("boton_marcar_todas");
        if (!lista) {
            return;
        }

        const generacion = generacion_sesion;
        cargando = true;
        if (resumen) {
            resumen.textContent = "Consultando notificaciones...";
        }
        if (boton_todas) {
            boton_todas.disabled = true;
        }
        utilidades.mostrar_carga(lista, "Cargando notificaciones...");

        try {
            const datos = await window.api_ucc.llamar(
                "notificaciones_listar"
            );
            if (generacion !== generacion_sesion) {
                return;
            }
            dibujar(datos);
        } catch (error) {
            if (generacion !== generacion_sesion) {
                return;
            }
            utilidades.mostrar_error(lista, error.message, cargar);
            if (resumen) {
                resumen.textContent = "No fue posible consultar la actividad.";
            }
        } finally {
            if (generacion === generacion_sesion) {
                cargando = false;
            }
        }
    }

    async function marcar_leida(id_notificacion, elemento) {
        if (elemento.disabled) {
            return;
        }
        const generacion = generacion_sesion;
        elemento.disabled = true;
        try {
            const datos = await window.api_ucc.llamar(
                "notificaciones_marcar_leida",
                { id_notificacion: id_notificacion }
            );
            if (generacion !== generacion_sesion) {
                return;
            }
            dibujar(datos);
        } catch (error) {
            if (generacion !== generacion_sesion) {
                return;
            }
            elemento.disabled = false;
            utilidades.toast(error.message, "error");
        }
    }

    async function marcar_todas() {
        const boton_todas = document.getElementById("boton_marcar_todas");
        if (!boton_todas || boton_todas.disabled) {
            return;
        }
        const generacion = generacion_sesion;
        utilidades.ocupar_boton(boton_todas, true, "Marcando...");
        try {
            const datos = await window.api_ucc.llamar(
                "notificaciones_marcar_todas"
            );
            if (generacion !== generacion_sesion) {
                return;
            }
            dibujar(datos);
            utilidades.toast(
                datos.mensaje || "Notificaciones marcadas como leídas.",
                "exito"
            );
        } catch (error) {
            if (generacion !== generacion_sesion) {
                return;
            }
            utilidades.toast(error.message, "error");
        } finally {
            if (generacion === generacion_sesion) {
                utilidades.ocupar_boton(boton_todas, false);
                boton_todas.disabled =
                    document.querySelectorAll(
                        "#lista_notificaciones .notificacion_no_leida"
                    ).length === 0;
            }
        }
    }

    function reiniciar() {
        generacion_sesion += 1;
        cargando = false;
        actualizar_contador(0);

        const lista = document.getElementById("lista_notificaciones");
        const resumen = document.getElementById("resumen_notificaciones");
        const boton_todas = document.getElementById("boton_marcar_todas");
        if (lista) {
            utilidades.vaciar(lista);
            lista.append(
                utilidades.estado_vacio(
                    "Abra el panel para consultar sus notificaciones.",
                    "bi-bell",
                    true
                )
            );
        }
        if (resumen) {
            resumen.textContent = "Consulte sus notificaciones.";
        }
        if (boton_todas) {
            utilidades.ocupar_boton(boton_todas, false);
            boton_todas.disabled = true;
        }
    }

    function iniciar() {
        if (iniciado) {
            return;
        }
        iniciado = true;

        const panel = document.getElementById("panel_notificaciones");
        const boton_todas = document.getElementById("boton_marcar_todas");
        const boton_notificaciones = document.getElementById(
            "boton_notificaciones"
        );

        if (panel) {
            panel.addEventListener("shown.bs.offcanvas", cargar);
        }
        if (boton_todas) {
            boton_todas.addEventListener("click", marcar_todas);
        }
        if (boton_notificaciones) {
            boton_notificaciones.addEventListener("click", function () {
                if (
                    typeof bootstrap === "undefined" ||
                    !bootstrap.Offcanvas
                ) {
                    cargar();
                }
            });
        }
    }

    return {
        iniciar: iniciar,
        cargar: cargar,
        reiniciar: reiniciar,
        actualizar_contador: actualizar_contador
    };
})();

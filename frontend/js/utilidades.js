window.utilidades_ucc = (function () {
    const ICONOS = {
        "bi-activity": "activity",
        "bi-arrow-clockwise": "rotate-cw",
        "bi-arrow-left": "arrow-left",
        "bi-arrow-right": "arrow-right",
        "bi-bar-chart": "chart-no-axes-column",
        "bi-bell": "bell",
        "bi-bell-slash": "bell-off",
        "bi-book": "book-open",
        "bi-box-arrow-in-right": "log-in",
        "bi-box-arrow-right": "log-out",
        "bi-calendar-check": "calendar-check",
        "bi-calendar-plus": "calendar-plus",
        "bi-calendar-x": "calendar-x",
        "bi-calendar3": "calendar-days",
        "bi-chat-check": "message-square-text",
        "bi-chat-left-dots": "message-circle-more",
        "bi-chat-left-text": "message-square-text",
        "bi-check-circle": "circle-check",
        "bi-check2": "check",
        "bi-check2-all": "check-check",
        "bi-check2-circle": "circle-check-big",
        "bi-check2-square": "square-check-big",
        "bi-circle": "circle",
        "bi-clipboard-check": "clipboard-check",
        "bi-clock": "clock",
        "bi-clock-history": "history",
        "bi-compass": "compass",
        "bi-envelope": "mail",
        "bi-exclamation-circle": "circle-alert",
        "bi-exclamation-triangle": "triangle-alert",
        "bi-eye": "eye",
        "bi-eye-slash": "eye-off",
        "bi-camera": "camera",
        "bi-foto": "camera",
        "bi-gear": "settings",
        "bi-image-up": "image-up",
        "bi-sliders": "sliders-horizontal",
        "bi-filter": "filter",
        "bi-graph-up-arrow": "trending-up",
        "bi-grid": "layout-grid",
        "bi-heart-pulse": "heart-pulse",
        "bi-hourglass-split": "hourglass",
        "bi-house-door": "house",
        "bi-inbox": "inbox",
        "bi-info-circle": "info",
        "bi-journal-bookmark": "book-marked",
        "bi-journal-x": "book-x",
        "bi-key": "key-round",
        "bi-list": "menu",
        "bi-list-check": "list-checks",
        "bi-lock": "lock",
        "bi-mortarboard": "graduation-cap",
        "bi-pen": "pen",
        "bi-people": "users",
        "bi-person-badge": "id-card",
        "bi-person-check": "user-check",
        "bi-person-plus": "user-plus",
        "bi-person-video3": "video",
        "bi-person-workspace": "briefcase-business",
        "bi-person-x": "user-x",
        "bi-plus-circle": "circle-plus",
        "bi-search": "search",
        "bi-send": "send",
        "bi-scroll-text": "scroll-text",
        "bi-send-check": "send",
        "bi-shield-check": "shield-check",
        "bi-shield-exclamation": "shield-alert",
        "bi-shield-lock": "lock-keyhole",
        "bi-x-circle": "circle-x",
        "bi-x-lg": "x"
    };
    const ESPACIO_SVG = "http://www.w3.org/2000/svg";
    const ESPACIO_XLINK = "http://www.w3.org/1999/xlink";
    const RUTA_SPRITE = "assets/iconos/lucide-sprite.svg";

    function crear(etiqueta, clase, texto) {
        const elemento = document.createElement(etiqueta);
        if (clase) {
            elemento.className = clase;
        }
        if (texto !== undefined && texto !== null) {
            elemento.textContent = String(texto);
        }
        return elemento;
    }

    function normalizar_icono(nombre) {
        const texto = String(nombre || "").trim();
        if (ICONOS[texto]) {
            return ICONOS[texto];
        }
        if (/^[a-z0-9-]+$/.test(texto)) {
            return texto;
        }
        return "circle";
    }

    function icono(nombre) {
        const clave = normalizar_icono(nombre);
        const elemento = document.createElementNS(ESPACIO_SVG, "svg");
        elemento.classList.add("icono_ucc");
        elemento.setAttribute("viewBox", "0 0 24 24");
        elemento.setAttribute("fill", "none");
        elemento.setAttribute("stroke", "currentColor");
        elemento.setAttribute("stroke-width", "1.8");
        elemento.setAttribute("stroke-linecap", "round");
        elemento.setAttribute("stroke-linejoin", "round");
        elemento.setAttribute("aria-hidden", "true");
        elemento.setAttribute("focusable", "false");
        const uso = document.createElementNS(ESPACIO_SVG, "use");
        const ruta = RUTA_SPRITE + "#" + clave;
        uso.setAttribute("href", ruta);
        uso.setAttributeNS(ESPACIO_XLINK, "xlink:href", ruta);
        elemento.append(uso);
        return elemento;
    }

    function reemplazar_icono(contenedor, nombre) {
        if (!contenedor) {
            return null;
        }
        const nuevo = icono(nombre);
        const actual = contenedor.querySelector(".icono_ucc");
        if (actual) {
            actual.replaceWith(nuevo);
        } else {
            contenedor.prepend(nuevo);
        }
        return nuevo;
    }

    function vaciar(elemento) {
        if (elemento) {
            elemento.replaceChildren();
        }
    }

    function boton(texto, nombre_icono, clase, al_hacer_clic) {
        const elemento = crear("button", clase || "boton_principal", texto);
        elemento.type = "button";
        if (nombre_icono) {
            elemento.prepend(icono(nombre_icono));
        }
        if (typeof al_hacer_clic === "function") {
            elemento.addEventListener("click", al_hacer_clic);
        }
        return elemento;
    }

    function limpiar_clase_estado(estado) {
        return String(estado || "")
            .toLowerCase()
            .replace(/[^a-z_]/g, "");
    }

    function etiqueta_estado(estado, texto) {
        const elemento = crear(
            "span",
            "etiqueta_estado estado_" + limpiar_clase_estado(estado),
            texto || estado || "Sin estado"
        );
        return elemento;
    }

    function etiqueta_neutra(texto) {
        return crear("span", "etiqueta_neutra", texto);
    }

    function estado_vacio(mensaje, nombre_icono, compacto) {
        const contenedor = crear(
            "div",
            "estado_vacio" + (compacto ? " compacto" : "")
        );
        contenedor.append(icono(nombre_icono || "bi-inbox"));
        const texto = crear("p", "", mensaje);
        contenedor.append(texto);
        return contenedor;
    }

    function mostrar_carga(contenedor, mensaje) {
        vaciar(contenedor);
        const bloque = crear("div", "cargando_bloque");
        bloque.setAttribute("role", "status");
        bloque.setAttribute("aria-live", "polite");
        const giro = crear("div", "spinner-border");
        giro.setAttribute("aria-hidden", "true");
        bloque.append(giro, crear("p", "", mensaje || "Cargando información..."));
        contenedor.append(bloque);
    }

    function mostrar_error(contenedor, mensaje, al_reintentar) {
        vaciar(contenedor);
        const bloque = crear("div", "error_bloque");
        bloque.setAttribute("role", "alert");
        bloque.append(icono("bi-exclamation-triangle"));
        bloque.append(
            crear(
                "p",
                "",
                typeof mensaje === "string"
                    ? mensaje
                    : "No fue posible cargar la información."
            )
        );
        if (typeof al_reintentar === "function") {
            const reintentar = boton(
                "Intentar nuevamente",
                "bi-arrow-clockwise",
                "boton_claro boton_pequeno",
                al_reintentar
            );
            bloque.append(reintentar);
        }
        contenedor.append(bloque);
    }

    async function cargar_vista(contenedor, accion, contexto, dibujar) {
        const esta_vigente = function () {
            return (
                !contexto ||
                typeof contexto.vigente !== "function" ||
                contexto.vigente()
            );
        };

        mostrar_carga(contenedor);
        try {
            const datos = await window.api_ucc.llamar(accion);
            if (!esta_vigente()) {
                return;
            }
            dibujar(datos);
        } catch (error) {
            if (!esta_vigente()) {
                return;
            }
            mostrar_error(contenedor, error.message, function () {
                cargar_vista(contenedor, accion, contexto, dibujar);
            });
        }
    }

    function mapa_iconos_alerta(tipo) {
        if (tipo === "alerta") {
            return "bi-exclamation-triangle";
        }
        if (tipo === "exito") {
            return "bi-check-circle";
        }
        return "bi-info-circle";
    }

    function alerta(mensaje, tipo, cerrable) {
        const nivel = tipo || "informacion";
        const caja = crear("div", "alerta_ucc tipo_" + nivel);
        caja.setAttribute("role", nivel === "alerta" ? "alert" : "status");
        caja.append(icono(mapa_iconos_alerta(nivel)));
        caja.append(crear("span", "alerta_ucc_texto", mensaje));
        if (cerrable !== false) {
            const cerrar = crear("button", "alerta_ucc_cerrar");
            cerrar.type = "button";
            cerrar.setAttribute("aria-label", "Cerrar mensaje");
            cerrar.append(icono("bi-x-lg"));
            cerrar.addEventListener("click", function () {
                caja.remove();
            });
            caja.append(cerrar);
        }
        return caja;
    }

    function lista_alertas(alertas) {
        const contenedor = crear("div", "lista_alertas");
        (alertas || []).forEach(function (item) {
            contenedor.append(alerta(item.texto, item.tipo));
        });
        return contenedor;
    }

    function toast(mensaje, tipo) {
        const zona = document.getElementById("zona_toasts");
        if (!zona) {
            return;
        }

        const nivel =
            tipo === "error" ? "error" : tipo === "exito" ? "exito" : "informacion";
        const elemento = crear("div", "toast_ucc tipo_" + nivel);
        elemento.setAttribute("role", "status");
        elemento.setAttribute("aria-live", "polite");
        elemento.append(
            icono(
                nivel === "error"
                    ? "bi-exclamation-circle"
                    : nivel === "exito"
                      ? "bi-check-circle"
                      : "bi-info-circle"
            )
        );
        elemento.append(crear("p", "", mensaje));

        const cerrar = crear("button", "");
        cerrar.type = "button";
        cerrar.setAttribute("aria-label", "Cerrar notificación");
        cerrar.append(icono("bi-x-lg"));
        cerrar.addEventListener("click", function () {
            elemento.remove();
        });
        elemento.append(cerrar);
        zona.append(elemento);

        window.setTimeout(function () {
            if (elemento.isConnected) {
                elemento.remove();
            }
        }, 6500);
    }

    function ocupar_boton(elemento, ocupado, texto_ocupado) {
        if (!elemento) {
            return;
        }
        if (ocupado) {
            if (!elemento.dataset.contenido_original) {
                elemento.dataset.contenido_original = "1";
                elemento.dataset.nodos_originales = "";
                elemento._nodos_originales = Array.from(elemento.childNodes).map(
                    function (nodo) {
                        return nodo.cloneNode(true);
                    }
                );
            }
            const giro = crear("span", "spinner-border spinner-border-sm");
            giro.setAttribute("aria-hidden", "true");
            elemento.replaceChildren(giro);
            elemento.append(
                document.createTextNode(
                    texto_ocupado ? " " + texto_ocupado : " Procesando..."
                )
            );
            elemento.disabled = true;
            elemento.setAttribute("aria-busy", "true");
        } else {
            if (elemento._nodos_originales) {
                elemento.replaceChildren(
                    ...elemento._nodos_originales.map(function (nodo) {
                        return nodo.cloneNode(true);
                    })
                );
            }
            delete elemento.dataset.contenido_original;
            delete elemento.dataset.nodos_originales;
            delete elemento._nodos_originales;
            elemento.disabled = false;
            elemento.removeAttribute("aria-busy");
        }
    }

    function convertir_celda(valor) {
        if (valor instanceof Node) {
            return valor;
        }
        if (Array.isArray(valor)) {
            const fragmento = document.createDocumentFragment();
            valor.forEach(function (item) {
                if (item) {
                    fragmento.append(item instanceof Node ? item : String(item));
                }
            });
            return fragmento;
        }
        return document.createTextNode(
            valor === undefined || valor === null ? "" : String(valor)
        );
    }

    function tabla(columnas, filas, titulo) {
        const contenedor = crear("div", "tabla_responsive");
        const elemento_tabla = crear("table", "tabla_ucc");
        if (titulo) {
            const leyenda = crear("caption", "visualmente_oculto", titulo);
            elemento_tabla.append(leyenda);
        }
        const cabeza = document.createElement("thead");
        const fila_cabeza = document.createElement("tr");
        columnas.forEach(function (columna) {
            const celda = document.createElement("th");
            celda.scope = "col";
            celda.textContent = columna.titulo || "";
            if (columna.clase) {
                celda.className = columna.clase;
            }
            fila_cabeza.append(celda);
        });
        cabeza.append(fila_cabeza);

        const cuerpo_tabla = document.createElement("tbody");
        filas.forEach(function (fila) {
            const fila_tabla = document.createElement("tr");
            columnas.forEach(function (columna) {
                const celda = document.createElement("td");
                if (columna.clase) {
                    celda.className = columna.clase;
                }
                let valor = fila;
                if (typeof columna.valor === "function") {
                    valor = columna.valor(fila);
                } else if (typeof columna.valor === "string") {
                    valor = fila[columna.valor];
                }
                celda.append(convertir_celda(valor));
                fila_tabla.append(celda);
            });
            cuerpo_tabla.append(fila_tabla);
        });

        elemento_tabla.append(cabeza, cuerpo_tabla);
        contenedor.append(elemento_tabla);
        return contenedor;
    }

    function lista_datos(datos) {
        const lista = crear("dl", "lista_datos");
        (datos || []).forEach(function (dato) {
            if (!dato) {
                return;
            }
            const fila = document.createElement("div");
            const termino = document.createElement("dt");
            termino.textContent = dato.etiqueta || "";
            const descripcion = document.createElement("dd");
            descripcion.append(
                convertir_celda(
                    dato.valor === undefined || dato.valor === null
                        ? "Sin información"
                        : dato.valor
                )
            );
            fila.append(termino, descripcion);
            lista.append(fila);
        });
        return lista;
    }

    function campo(opciones) {
        const configuracion = opciones || {};
        const grupo = crear("div", "campo_formulario");
        const id =
            configuracion.id ||
            "campo_" + Math.random().toString(36).slice(2, 10);
        const etiqueta = crear(
            "label",
            "form-label",
            configuracion.etiqueta || "Campo"
        );
        etiqueta.htmlFor = id;

        let control;
        const tipo = configuracion.tipo || "text";
        if (tipo === "select") {
            control = document.createElement("select");
            control.className = "form-select";
            if (configuracion.placeholder !== false) {
                const inicial = document.createElement("option");
                inicial.value = "";
                inicial.textContent =
                    configuracion.placeholder || "Seleccione una opción";
                control.append(inicial);
            }
            (configuracion.opciones || []).forEach(function (opcion) {
                const elemento_opcion = document.createElement("option");
                if (typeof opcion === "string") {
                    elemento_opcion.value = opcion;
                    elemento_opcion.textContent = opcion;
                } else {
                    elemento_opcion.value = opcion.valor;
                    elemento_opcion.textContent = opcion.texto;
                }
                control.append(elemento_opcion);
            });
        } else if (tipo === "textarea") {
            control = document.createElement("textarea");
            control.className = "form-control";
            control.rows = configuracion.filas || 4;
        } else {
            control = document.createElement("input");
            control.className = "form-control";
            control.type = tipo;
        }

        control.id = id;
        control.name = configuracion.nombre || id;
        if (configuracion.valor !== undefined && configuracion.valor !== null) {
            control.value = String(configuracion.valor);
        }
        if (configuracion.placeholder_texto) {
            control.placeholder = configuracion.placeholder_texto;
        }
        if (configuracion.required) {
            control.required = true;
        }
        if (configuracion.disabled) {
            control.disabled = true;
        }
        if (configuracion.readonly) {
            control.readOnly = true;
        }
        if (configuracion.min !== undefined) {
            control.min = configuracion.min;
        }
        if (configuracion.max !== undefined) {
            control.max = configuracion.max;
        }
        if (configuracion.step !== undefined) {
            control.step = configuracion.step;
        }
        if (configuracion.minlength !== undefined) {
            control.minLength = configuracion.minlength;
        }
        if (configuracion.maxlength !== undefined) {
            control.maxLength = configuracion.maxlength;
        }
        if (configuracion.pattern) {
            control.pattern = configuracion.pattern;
        }
        if (configuracion.title) {
            control.title = configuracion.title;
        }
        if (configuracion.autocomplete) {
            control.autocomplete = configuracion.autocomplete;
        }
        if (configuracion.inputmode) {
            control.inputMode = configuracion.inputmode;
        }

        if (configuracion.ayuda) {
            const id_ayuda = id + "_ayuda";
            control.setAttribute("aria-describedby", id_ayuda);
            grupo.append(etiqueta, control);
            const ayuda = crear("p", "campo_ayuda", configuracion.ayuda);
            ayuda.id = id_ayuda;
            grupo.append(ayuda);
        } else {
            grupo.append(etiqueta, control);
        }

        if (configuracion.ancho) {
            grupo.classList.add("campo_ancho");
        }
        if (configuracion.clase_grupo) {
            grupo.classList.add(configuracion.clase_grupo);
        }

        return {
            grupo: grupo,
            control: control
        };
    }

    function encabezado(titulo, descripcion, etiqueta, acciones) {
        // Sin subtítulo descriptivo: solo etiqueta + título.
        const contenedor = crear("div", "vista_encabezado");
        const texto = crear("div", "vista_encabezado_texto");
        if (etiqueta) {
            const superior = crear("p", "etiqueta_vista", etiqueta);
            texto.append(superior);
        }
        texto.append(crear("h2", "", titulo));
        contenedor.append(texto);
        if (acciones) {
            const zona_acciones = crear("div", "vista_acciones");
            zona_acciones.append(acciones);
            contenedor.append(zona_acciones);
        }
        return contenedor;
    }

    function acordeon_riesgo(opciones) {
        const op = opciones || {};
        const acordeon = crear("div", "accordion acordeon_ucc");
        acordeon.id = "acordeon_" + (op.id || "riesgo");
        (op.listas || []).forEach(function (lista, indice) {
            const item = crear("div", "accordion-item");
            const cabecera = crear("h3", "accordion-header");
            cabecera.id = op.id + "_cabecera_" + indice;
            const boton_acordeon = crear("button", "accordion-button collapsed");
            boton_acordeon.type = "button";
            boton_acordeon.setAttribute("data-bs-toggle", "collapse");
            boton_acordeon.setAttribute("data-bs-target", "#" + op.id + "_cuerpo_" + indice);
            boton_acordeon.setAttribute("aria-expanded", "false");
            boton_acordeon.setAttribute("aria-controls", op.id + "_cuerpo_" + indice);
            const lineas = op.titulo(lista);
            const titulo = document.createElement("span");
            titulo.append(
                crear("strong", "", lineas[0]),
                document.createElement("br"),
                crear("small", "texto_secundario", lineas[1])
            );
            const resumen = crear("span", "resumen_acordeon");
            resumen.append(
                crear("span", "", (lista.estudiantes || []).length + " estudiante(s)"),
                etiqueta_estado(lista.estado, lista.estado_texto)
            );
            boton_acordeon.append(titulo, resumen);
            cabecera.append(boton_acordeon);
            const colapsable = crear("div", "accordion-collapse collapse");
            colapsable.id = op.id + "_cuerpo_" + indice;
            colapsable.setAttribute("aria-labelledby", op.id + "_cabecera_" + indice);
            colapsable.setAttribute("data-bs-parent", "#acordeon_" + op.id);
            const cuerpo = crear("div", "accordion-body");
            cuerpo.append(lista_datos(op.filas(lista)));
            if (typeof op.accion === "function") {
                const cfg = op.accion(lista);
                if (cfg) {
                    const barra = crear("div", "acciones_formulario acciones_formulario_inicio");
                    const boton_accion = boton(cfg.texto, cfg.icono, cfg.clase);
                    boton_accion.addEventListener("click", async function () {
                        ocupar_boton(boton_accion, true, cfg.ocupado || "Procesando...");
                        try {
                            const peticion = cfg.llamar(lista);
                            const respuesta = await window.api_ucc.llamar(peticion.accion, peticion.datos);
                            if (op.contexto && !op.contexto.vigente()) {
                                return;
                            }
                            toast(respuesta.mensaje || cfg.ok || "Listo.", "exito");
                            if (typeof cfg.despues === "function") {
                                cfg.despues(respuesta);
                            }
                        } catch (error) {
                            if (op.contexto && !op.contexto.vigente()) {
                                return;
                            }
                            toast(error.message, "error");
                            ocupar_boton(boton_accion, false);
                        }
                    });
                    barra.append(boton_accion);
                    cuerpo.append(barra);
                }
            }
            const tabla_riesgo = tabla(op.columnas, lista.estudiantes || [], op.leyenda || "Estudiantes en riesgo");
            tabla_riesgo.style.marginTop = "14px";
            cuerpo.append(tabla_riesgo);
            colapsable.append(cuerpo);
            item.append(cabecera, colapsable);
            acordeon.append(item);
        });
        return acordeon;
    }

    function tarjeta_revision(op) {
        const tarjeta = crear("article", "informe_tarjeta");
        const encabezado = crear("div", "informe_tarjeta_encabezado");
        const datos_titulo = document.createElement("div");
        datos_titulo.append(
            crear("h4", "", op.titulo),
            crear("p", "", op.subtitulo)
        );
        encabezado.append(
            datos_titulo,
            etiqueta_estado(op.estado[0], op.estado[1])
        );

        const cuerpo = crear("div", "informe_cuerpo");
        const meta = crear("div", "informe_meta");
        (op.meta || []).forEach(function (dato) {
            const elemento = document.createElement("span");
            elemento.append(
                icono(dato[0]),
                document.createTextNode(dato[1])
            );
            meta.append(elemento);
        });
        cuerpo.append(meta);
        (op.bloques || []).forEach(function (bloque) {
            const caja = crear("div", bloque.clase || "informe_actividades");
            caja.append(
                crear("strong", "", bloque.titulo),
                document.createTextNode(bloque.texto)
            );
            cuerpo.append(caja);
        });
        (op.alertas || []).forEach(function (texto) {
            cuerpo.append(alerta(texto, "alerta"));
        });
        if (op.firma) {
            const firma = crear("div", "firma_informe");
            firma.append(icono("bi-pen"));
            firma.append(document.createTextNode("Firma del profesor: " + op.firma));
            cuerpo.append(firma);
        }

        const revision = crear("div", "informe_revision");
        const entrada = campo({
            id: op.campo.id,
            etiqueta: op.campo.etiqueta,
            tipo: "textarea",
            filas: 3,
            maxlength: op.campo.max || 500,
            placeholder_texto: op.campo.placeholder,
            ayuda: op.campo.ayuda
        });
        const mensaje = crear("p", "mensaje_validacion");
        mensaje.hidden = true;
        const acciones = crear("div", "informe_acciones");
        const boton_no = boton("Rechazar", "bi-x-circle", "boton_peligro boton_pequeno");
        const boton_si = boton(op.boton_ok || "Aprobar", op.icono_ok || "bi-check2-circle", "boton_exito boton_pequeno");
        if (op.ok_deshabilitado) {
            boton_si.disabled = true;
        }

        async function decidir(decision, boton_pulsado) {
            const texto = entrada.control.value.trim();
            mensaje.hidden = true;
            mensaje.textContent = "";
            const fallo = op.validar ? op.validar(texto, decision) : null;
            if (fallo) {
                mensaje.textContent = fallo;
                mensaje.hidden = false;
                entrada.control.focus();
                return;
            }
            ocupar_boton(boton_pulsado, true, "Enviando...");
            boton_si.disabled = true;
            boton_no.disabled = true;
            try {
                const peticion = op.llamar(texto, decision);
                const respuesta = await window.api_ucc.llamar(peticion.accion, peticion.datos);
                if (op.contexto && !op.contexto.vigente()) {
                    return;
                }
                toast(respuesta.mensaje || op.ok_msg || "Listo.", "exito");
                if (typeof op.despues === "function") {
                    op.despues(respuesta);
                }
            } catch (error) {
                if (op.contexto && !op.contexto.vigente()) {
                    return;
                }
                mensaje.textContent = error.message;
                mensaje.hidden = false;
                toast(error.message, "error");
                ocupar_boton(boton_pulsado, false);
                boton_si.disabled = !!op.ok_deshabilitado;
                boton_no.disabled = false;
            }
        }

        boton_no.addEventListener("click", function () {
            decidir("rechazar", boton_no);
        });
        boton_si.addEventListener("click", function () {
            decidir("aprobar", boton_si);
        });
        acciones.append(mensaje, boton_no, boton_si);
        revision.append(entrada.grupo, acciones);
        tarjeta.append(encabezado, cuerpo, revision);
        return tarjeta;
    }

    function icono_alerta(tipo) {
        if (tipo === "exito") {
            return "bi-check-circle";
        }
        if (tipo === "alerta") {
            return "bi-exclamation-triangle";
        }
        return "bi-info-circle";
    }

    function tarjeta_metrica(tarjeta) {
        const elemento = crear(
            "article",
            "tarjeta_metrica tipo_" + (tarjeta.tipo || "azul")
        );
        const fila = crear("div", "tarjeta_metrica_fila");
        const contenido = document.createElement("div");
        contenido.append(
            crear("p", "tarjeta_metrica_titulo", tarjeta.titulo),
            crear("p", "tarjeta_metrica_valor", tarjeta.valor),
            crear("p", "tarjeta_metrica_detalle", tarjeta.detalle)
        );
        const caja_icono = crear("div", "tarjeta_metrica_icono");
        caja_icono.append(icono(tarjeta.icono || "bi-bar-chart"));
        fila.append(contenido, caja_icono);
        elemento.append(fila);
        return elemento;
    }

    function texto_horas(valor) {
        const numero = Number(valor);
        if (!Number.isFinite(numero)) {
            return "0 horas";
        }
        return numero === 1 ? "1 hora" : numero + " horas";
    }

    function iniciales(nombre) {
        return String(nombre || "U")
            .trim()
            .split(/\s+/)
            .slice(0, 2)
            .map(function (parte) {
                return parte.charAt(0).toUpperCase();
            })
            .join("");
    }

    return {
        crear: crear,
        icono: icono,
        reemplazar_icono: reemplazar_icono,
        vaciar: vaciar,
        boton: boton,
        etiqueta_estado: etiqueta_estado,
        etiqueta_neutra: etiqueta_neutra,
        estado_vacio: estado_vacio,
        mostrar_carga: mostrar_carga,
        mostrar_error: mostrar_error,
        cargar_vista: cargar_vista,
        alerta: alerta,
        lista_alertas: lista_alertas,
        toast: toast,
        ocupar_boton: ocupar_boton,
        tabla: tabla,
        lista_datos: lista_datos,
        campo: campo,
        encabezado: encabezado,
        tarjeta_metrica: tarjeta_metrica,
        icono_alerta: icono_alerta,
        acordeon_riesgo: acordeon_riesgo,
        tarjeta_revision: tarjeta_revision,
        texto_horas: texto_horas,
        iniciales: iniciales
    };
})();

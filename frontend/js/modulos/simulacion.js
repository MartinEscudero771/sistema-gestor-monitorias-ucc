window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    const COLOR_BARRA = "#00acc9";
    const COLOR_BARRA_ALT = "#132740";
    const COLOR_EJE = "#64727d";
    const COLOR_REJILLA = "#dce5ea";
    const FUENTE_WEB = "11px \"Segoe UI\", sans-serif";

    let simulando = false;

    function texto_numero(valor, decimales) {
        const numero = Number(valor);
        if (!Number.isFinite(numero)) {
            return "0";
        }
        return numero.toLocaleString("es-CO", {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales
        });
    }

    function preparar_lienzo(lienzo, ancho, alto) {
        const factor = window.devicePixelRatio || 1;
        const ancho_real = lienzo.clientWidth || ancho || 640;
        const alto_real = lienzo.clientHeight || alto || 260;
        lienzo.width = ancho_real * factor;
        lienzo.height = alto_real * factor;
        const contexto = lienzo.getContext("2d");
        contexto.scale(factor, factor);
        contexto.clearRect(0, 0, ancho_real, alto_real);
        contexto.font = FUENTE_WEB;
        contexto.fillStyle = COLOR_EJE;
        return {
            contexto: contexto,
            ancho: ancho_real,
            alto: alto_real
        };
    }

    function dibujar_eje(contexto, zona, maximo, formato) {
        [0, 0.5, 1].forEach(function (fraccion) {
            const y_linea = zona.y + zona.h - fraccion * zona.h;
            contexto.strokeStyle = COLOR_REJILLA;
            contexto.beginPath();
            contexto.moveTo(zona.x, y_linea);
            contexto.lineTo(zona.x + zona.w, y_linea);
            contexto.stroke();
            contexto.fillStyle = COLOR_EJE;
            contexto.fillText(
                formato(maximo * fraccion),
                2,
                y_linea + 4
            );
        });
    }

    function dibujar_histograma(lienzo, bins) {
        const lienzo_info = preparar_lienzo(lienzo, 640, 260);
        const contexto = lienzo_info.contexto;

        const margen_izq = 30;
        const margen_abajo = 34;
        const margen_arriba = 12;
        const zona = {
            x: margen_izq,
            y: margen_arriba,
            w: lienzo_info.ancho - margen_izq - 8,
            h: lienzo_info.alto - margen_arriba - margen_abajo
        };

        let maximo = 0;
        bins.forEach(function (bin) {
            maximo = Math.max(maximo, bin.cuenta);
        });
        dibujar_eje(contexto, zona, Math.max(maximo, 1), function (valor) {
            return String(Math.round(valor));
        });

        const ancho_barra = bins.length ? zona.w / bins.length : 0;
        bins.forEach(function (bin, indice) {
            const altura = (bin.cuenta / Math.max(maximo, 1)) * zona.h;
            const x = zona.x + indice * ancho_barra;
            const y = zona.y + zona.h - altura;
            contexto.fillStyle =
                indice % 2 === 0 ? COLOR_BARRA : COLOR_BARRA_ALT;
            if (bin.cuenta > 0) {
                contexto.fillRect(
                    x + 2,
                    y,
                    Math.max(ancho_barra - 4, 2),
                    Math.max(altura, 2)
                );
                contexto.fillStyle = COLOR_EJE;
                contexto.fillText(
                    String(bin.cuenta),
                    x + ancho_barra / 2 - 5,
                    y - 4
                );
            }
            contexto.fillStyle = COLOR_EJE;
            contexto.fillText(
                texto_numero(bin.inicio, 1),
                x - 4,
                zona.y + zona.h + 14
            );
        });
        contexto.fillText(
            "Horas de espera media por repetición",
            zona.x,
            zona.y + zona.h + 29
        );
    }

    function dibujar_linea_capacidad(lienzo, lineas) {
        const lienzo_info = preparar_lienzo(lienzo, 640, 260);
        const contexto = lienzo_info.contexto;

        const zona = {
            x: 34,
            y: 14,
            w: lienzo_info.ancho - 44,
            h: lienzo_info.alto - 48
        };

        let maximo = 0;
        lineas.forEach(function (punto) {
            maximo = Math.max(maximo, punto.y);
        });
        dibujar_eje(contexto, zona, Math.max(maximo, 0.5), function (
            valor
        ) {
            return texto_numero(valor, 1);
        });

        const paso_x = lineas.length > 1
            ? zona.w / (lineas.length - 1)
            : 0;
        const escala_y = function (valor) {
            return zona.y + zona.h - (valor / Math.max(maximo, 0.5)) * zona.h;
        };

        contexto.strokeStyle = COLOR_BARRA;
        contexto.lineWidth = 2;
        contexto.beginPath();
        lineas.forEach(function (punto, indice) {
            const x = zona.x + indice * paso_x;
            const y = escala_y(punto.y);
            if (indice === 0) {
                contexto.moveTo(x, y);
            } else {
                contexto.lineTo(x, y);
            }
        });
        contexto.stroke();

        lineas.forEach(function (punto, indice) {
            const x = zona.x + indice * paso_x;
            const y = escala_y(punto.y);
            contexto.fillStyle = COLOR_BARRA_ALT;
            contexto.beginPath();
            contexto.arc(x, y, 4, 0, Math.PI * 2);
            contexto.fill();
            contexto.fillStyle = COLOR_EJE;
            contexto.fillText(punto.etiqueta, x - 28, zona.y + zona.h + 16);
        });
        contexto.fillText(
            "Espera media (h) según número de monitores",
            zona.x,
            zona.y + zona.h + 30
        );
    }

    function leyenda_texto(resultado) {
        const bins = resultado.histograma || [];
        if (!bins.length) {
            return "Sin datos de espera para graficar.";
        }
        return (
            "Cada barra cuenta repeticiones cuyo tiempo medio de espera cayó en el " +
            "intervalo; el eje horizontal cubre de " +
            texto_numero(bins[0].inicio, 1) +
            " a " +
            texto_numero(bins[bins.length - 1].fin, 1) +
            " horas."
        );
    }

    function crear_lienzo(atributo_etiqueta) {
        const lienzo = document.createElement("canvas");
        lienzo.className = "lienzo_histograma";
        lienzo.setAttribute("role", "img");
        lienzo.setAttribute("aria-label", atributo_etiqueta);
        return lienzo;
    }

    function pintar_resultado(zona, resultado) {
        utilidades.vaciar(zona);
        const resumen = resultado.resumen || {};
        const parametros = resultado.parametros || {};

        const metricas = utilidades.crear("div", "tarjetas_metricas");
        metricas.append(
            utilidades.tarjeta_metrica({
                titulo: "Atendidos",
                valor: texto_numero(resumen.atendidos_media, 1),
                detalle: "sesiones que terminan por repetición (media)",
                icono: "bi-check2-circle",
                tipo: "verde"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Desistidos",
                valor: texto_numero(resumen.desistidos_media, 1),
                detalle: "abandonaron la cola tras superar el umbral de espera",
                icono: "bi-exclamation-triangle",
                tipo: "amarillo"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Espera media",
                valor: texto_numero(resumen.espera_media_horas, 2) + " h",
                detalle:
                    "mediana " +
                    texto_numero(resumen.espera_mediana_horas, 2) +
                    " h · p95 " +
                    texto_numero(resumen.espera_p95_horas, 2) +
                    " h",
                icono: "bi-clock",
                tipo: "azul"
            }),
            utilidades.tarjeta_metrica({
                titulo: "Utilización",
                valor:
                    texto_numero((resumen.utilizacion_media || 0) * 100, 1) +
                    "%",
                detalle: "fracción de horas de monitor realmente usadas",
                icono: "bi-bar-chart",
                tipo: "azul_diversidad"
            })
        );

        const caja_grafico = utilidades.crear(
            "div",
            "tarjeta_config simulacion_informe"
        );
        const lienzo = crear_lienzo(
            "Histograma del tiempo medio de espera en " +
                (resultado.repeticiones || []).length +
                " repeticiones"
        );
        window.requestAnimationFrame(function () {
            dibujar_histograma(lienzo, resultado.histograma || []);
        });
        caja_grafico.append(
            utilidades.crear("h3", "etiqueta_vista", "Distribución de esperas"),
            utilidades.crear(
                "p",
                "texto_secundario",
                leyenda_texto(resultado)
            ),
            lienzo
        );

        const caja_detalle = utilidades.crear(
            "div",
            "tarjeta_config simulacion_informe"
        );
        caja_detalle.append(
            utilidades.crear("h3", "etiqueta_vista", "Detalle por repetición"),
            utilidades.tabla(
                [
                    { titulo: "#", valor: "repeticion", clase: "col_corta" },
                    { titulo: "Llegadas", valor: "llegadas" },
                    { titulo: "Atendidos", valor: "atendidos" },
                    { titulo: "Desistidos", valor: "desistidos" },
                    { titulo: "Cola final", valor: "en_cola_final" },
                    {
                        titulo: "Espera media",
                        valor: function (fila) {
                            return (
                                texto_numero(fila.espera_media_horas, 2) + " h"
                            );
                        }
                    },
                    {
                        titulo: "Utilización",
                        valor: function (fila) {
                            return (
                                texto_numero(fila.utilizacion * 100, 1) + "%"
                            );
                        }
                    }
                ],
                resultado.repeticiones || [],
                "Detalle de repeticiones de la simulación"
            )
        );

        zona.append(
            utilidades.encabezado(
                "Escenario simulado",
                "",
                "Corrida con " +
                    parametros.dias_simulados +
                    " días y " +
                    parametros.repeticiones +
                    " repeticiones (semilla " +
                    parametros.semilla +
                    ")"
            ),
            metricas,
            utilidades.alerta(
                resultado.nota || "Simulación completada.",
                "informacion",
                false
            )
        );
        const graficos = utilidades.crear("div", "simulacion_graficos");
        graficos.append(caja_grafico, caja_detalle);
        zona.append(graficos);
    }

    function pintar_comparacion(zona, datos) {
        utilidades.vaciar(zona);
        const comparacion = datos.comparacion || [];

        const lineas = comparacion.map(function (fila) {
            return {
                y: fila.espera_media_horas || 0,
                etiqueta: fila.num_monitores + " monitor(es)"
            };
        });

        const tarjetas = utilidades.crear("div", "tarjetas_metricas");
        let mejor = null;
        comparacion.forEach(function (fila) {
            if (!mejor || fila.espera_media_horas < mejor.espera_media_horas) {
                mejor = fila;
            }
        });
        if (mejor) {
            tarjetas.append(
                utilidades.tarjeta_metrica({
                    titulo: "Mejor capacidad",
                    valor: String(mejor.num_monitores),
                    detalle:
                        "monitor(es): espera media " +
                        texto_numero(mejor.espera_media_horas, 2) +
                        " h con utilización del " +
                        texto_numero(mejor.utilizacion_media * 100, 1) +
                        "%",
                    icono: "bi-graph-up-arrow",
                    tipo: "verde"
                })
            );
        }

        const caja_comparacion = utilidades.crear(
            "div",
            "tarjeta_config simulacion_informe"
        );
        const lienzo = crear_lienzo(
            "Espera media de los estudiantes según el número de monitores"
        );
        window.requestAnimationFrame(function () {
            dibujar_linea_capacidad(lienzo, lineas);
        });
        caja_comparacion.append(
            utilidades.crear(
                "h3",
                "etiqueta_vista",
                "Comparación de capacidad"
            ),
            utilidades.crear("p", "texto_secundario", datos.nota || ""),
            lienzo,
            utilidades.tabla(
                [
                    {
                        titulo: "Monitores",
                        valor: "num_monitores",
                        clase: "col_corta"
                    },
                    {
                        titulo: "Espera media",
                        valor: function (fila) {
                            return (
                                texto_numero(fila.espera_media_horas, 2) + " h"
                            );
                        }
                    },
                    {
                        titulo: "Espera p95",
                        valor: function (fila) {
                            return (
                                texto_numero(fila.espera_p95_horas, 2) + " h"
                            );
                        }
                    },
                    {
                        titulo: "Utilización",
                        valor: function (fila) {
                            return (
                                texto_numero(fila.utilizacion_media * 100, 1) +
                                "%"
                            );
                        }
                    },
                    {
                        titulo: "Atendidos", 
                        valor: function (fila) {
                            return texto_numero(fila.atendidos_media, 1);
                        }
                    },
                    {
                        titulo: "Desistidos",
                        valor: function (fila) {
                            return texto_numero(fila.desistidos_media, 1);
                        }
                    }
                ],
                comparacion,
                "Comparación de capacidad de monitores"
            )
        );

        zona.append(
            utilidades.encabezado("Comparación de capacidad", ""),
            tarjetas,
            caja_comparacion
        );
    }

    function pintar_zona_vacia(zona) {
        utilidades.vaciar(zona);
        zona.append(
            utilidades.estado_vacio(
                "Configure los parámetros y ejecute la simulación para ver el escenario.",
                "bi-activity",
                true
            )
        );
    }

    async function ejecutar(boton, dentro, campos_param, zona) {
        if (simulando || !dentro.vigente()) {
            return;
        }
        const parametros = leer_parametros(campos_param);
        let hay_error = false;
        Object.keys(parametros).forEach(function (clave) {
            if (parametros[clave] === null) {
                hay_error = true;
            }
        });
        if (hay_error) {
            utilidades.toast(
                "Revise los parámetros: hay valores fuera de los rangos permitidos.",
                "error"
            );
            return;
        }

        simulando = true;
        utilidades.ocupar_boton(boton, true, "Calculando...");
        utilidades.mostrar_carga(zona, "Ejecutando la simulación...");
        try {
            const accion =
                boton.dataset.modo === "comparar"
                    ? "simulacion_comparar"
                    : "simulacion_ejecutar";
            const resultado = await api.llamar(accion, parametros);
            if (!dentro.vigente()) {
                return;
            }
            if (accion === "simulacion_comparar") {
                pintar_comparacion(zona, resultado);
            } else {
                pintar_resultado(zona, resultado);
            }
        } catch (error) {
            if (dentro.vigente()) {
                pintar_zona_vacia(zona);
                utilidades.toast(error.message, "error");
            }
        } finally {
            simulando = false;
            if (dentro.vigente()) {
                utilidades.ocupar_boton(boton, false);
            }
        }
    }

    function leer_parametros(campos_param) {
        const valor_de = function (control, por_defecto, minimo, maximo) {
            const crudo = String(control.value || "").trim();
            if (crudo === "") {
                return por_defecto;
            }
            const numero = Number(crudo);
            if (
                !Number.isFinite(numero) ||
                numero < minimo ||
                numero > maximo
            ) {
                return null;
            }
            return numero;
        };
        return {
            num_monitores: valor_de(campos_param.monitores.control, 2, 1, 10),
            llegadas_diarias: valor_de(campos_param.llegadas.control, 16, 0.5, 40),
            duracion_media_horas: valor_de(
                campos_param.duracion.control,
                1.5,
                0.5,
                3
            ),
            dias_simulados: valor_de(campos_param.dias.control, 21, 7, 42),
            repeticiones: valor_de(
                campos_param.repeticiones.control,
                8,
                1,
                30
            ),
            semilla: valor_de(campos_param.semilla.control, 42, 0, 4294967295)
        };
    }

    function construir_formulario() {
        return {
            monitores: utilidades.campo({
                id: "sim_monitores",
                etiqueta: "Monitores disponibles (c)",
                tipo: "select",
                valor: 2,
                opciones: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                ayuda: "Número de monitores atendiendo la cola cada hora de jornada."
            }),
            llegadas: utilidades.campo({
                id: "sim_llegadas",
                etiqueta: "Llegadas por día",
                tipo: "number",
                valor: 16,
                min: 0.5,
                max: 40,
                step: 0.5,
                ayuda:
                    "Media de solicitudes nuevas por día (se reparte con Poisson por hora)."
            }),
            duracion: utilidades.campo({
                id: "sim_duracion",
                etiqueta: "Duración media (h)",
                tipo: "number",
                valor: 1.5,
                min: 0.5,
                max: 3,
                step: 0.5,
                ayuda:
                    "Duración media de la sesión: se sortea exponencial y se recorta entre 0,5 y 4 h."
            }),
            dias: utilidades.campo({
                id: "sim_dias",
                etiqueta: "Días simulados",
                tipo: "number",
                valor: 21,
                min: 7,
                max: 42,
                step: 1
            }),
            repeticiones: utilidades.campo({
                id: "sim_repeticiones",
                etiqueta: "Repeticiones",
                tipo: "number",
                valor: 8,
                min: 1,
                max: 30,
                step: 1,
                ayuda:
                    "Corridas independientes con semillas derivadas: más repeticiones dan estadística más estable."
            }),
            semilla: utilidades.campo({
                id: "sim_semilla",
                etiqueta: "Semilla",
                tipo: "number",
                valor: 42,
                min: 0,
                max: 4294967295,
                step: 1,
                ayuda:
                    "Con la misma semilla el escenario se reproduce de forma idéntica."
            })
        };
    }

    window.vistas_ucc.simulacion = async function (contenedor, contexto) {
        const dentro = contexto;
        utilidades.vaciar(contenedor);
        contenedor.append(
            utilidades.encabezado(
                "Simulación de demanda",
                "simulacion",
                "Laboratorio de escenarios"
            )
        );

        const grid = utilidades.crear("div", "simulacion_grid");
        const formulario = utilidades.crear("section", "tarjeta_config");
        formulario.append(
            utilidades.crear(
                "h3",
                "etiqueta_vista",
                "Parámetros del escenario"
            )
        );
        const campos_param = construir_formulario();
        formulario.append(
            campos_param.monitores.grupo,
            campos_param.llegadas.grupo,
            campos_param.duracion.grupo,
            campos_param.dias.grupo,
            campos_param.repeticiones.grupo,
            campos_param.semilla.grupo
        );

        const acciones = utilidades.crear("div", "grupo_botones");
        const boton_ejecutar = utilidades.boton(
            "Ejecutar simulación",
            "bi-activity",
            "boton_principal"
        );
        boton_ejecutar.dataset.modo = "ejecutar";
        const boton_comparar = utilidades.boton(
            "Comparar capacidad (1 a 4 monitores)",
            "bi-graph-up-arrow",
            "boton_claro"
        );
        boton_comparar.dataset.modo = "comparar";
        acciones.append(boton_ejecutar, boton_comparar);
        formulario.append(acciones);

        grid.append(formulario);
        contenedor.append(grid);

        const zona_resultados = utilidades.crear(
            "section",
            "zona_resultados_simulacion"
        );
        pintar_zona_vacia(zona_resultados);
        contenedor.append(zona_resultados);

        boton_ejecutar.addEventListener("click", function () {
            ejecutar(boton_ejecutar, dentro, campos_param, zona_resultados);
        });
        boton_comparar.addEventListener("click", function () {
            ejecutar(boton_comparar, dentro, campos_param, zona_resultados);
        });
    };
})();

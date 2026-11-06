window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    function escapar_csv(valor) {
        // Excel en español separa con ; y necesita BOM UTF-8.
        const texto = valor === undefined || valor === null ? "" : String(valor);
        if (texto.indexOf(";") !== -1 || texto.indexOf('"') !== -1 || texto.indexOf("\n") !== -1) {
            return '"' + texto.replace(/"/g, '""') + '"';
        }
        return texto;
    }

    function descargar_csv(nombre, cabeceras, filas) {
        const lineas = [cabeceras.map(escapar_csv).join(";")];
        filas.forEach(function (fila) {
            lineas.push(cabeceras.map(function (col) { return escapar_csv(fila[col]); }).join(";"));
        });
        const blob = new Blob(["\uFEFF" + lineas.join("\r\n")], { type: "text/csv;charset=utf-8" });
        const enlace = document.createElement("a");
        enlace.href = URL.createObjectURL(blob);
        enlace.download = nombre;
        document.body.append(enlace);
        enlace.click();
        enlace.remove();
        setTimeout(function () { URL.revokeObjectURL(enlace.href); }, 2000);
    }

    function escapar_html(valor) {
        return String(valor === undefined || valor === null ? "" : valor)
            .replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function tabla_html(titulo, cabeceras, filas) {
        let html = "<h2>" + escapar_html(titulo) + "</h2><table><thead><tr>";
        cabeceras.forEach(function (c) { html += "<th>" + escapar_html(c) + "</th>"; });
        html += "</tr></thead><tbody>";
        filas.forEach(function (f) {
            html += "<tr>";
            cabeceras.forEach(function (c) { html += "<td>" + escapar_html(f[c]) + "</td>"; });
            html += "</tr>";
        });
        return html + "</tbody></table>";
    }

    function exportar_pdf(horas, por_asignatura, por_estado) {
        const ventana = window.open("", "_blank", "width=900,height=700");
        if (!ventana) {
            utilidades.toast("Permita ventanas emergentes para exportar el PDF.", "error");
            return;
        }
        ventana.document.write(
            "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>" +
            "<title>Reporte de monitorías UCC</title>" +
            "<style>body{font-family:Arial,sans-serif;margin:32px;color:#1d2a35}" +
            "h1{color:#132740}h2{color:#132740;margin-top:28px}" +
            "table{border-collapse:collapse;width:100%;font-size:12px}" +
            "th,td{border:1px solid #999;padding:6px 8px;text-align:left}" +
            "th{background:#132740;color:#fff}p{color:#555}</style></head><body>" +
            "<h1>Reporte de monitorías — UCC</h1>" +
            "<p>Generado el " + escapar_html(new Date().toLocaleString("es-CO")) + "</p>" +
            tabla_html("Horas por monitor",
                ["monitor", "asignatura", "horas", "informes"], horas.filas || []) +
            tabla_html("Monitorías por asignatura",
                ["asignatura", "total", "programadas", "realizadas"], por_asignatura.filas || []) +
            tabla_html("Solicitudes por estado",
                ["estado", "total"], por_estado.filas || []) +
            "</body></html>"
        );
        ventana.document.close();
        ventana.focus();
        setTimeout(function () { ventana.print(); }, 400);
    }

    window.vistas_ucc.reportes = async function (contenedor, contexto) {
        utilidades.mostrar_carga(contenedor, "Cargando reporte de monitorías...");
        let horas = { filas: [] };
        let por_asignatura = { filas: [] };
        let por_estado = { filas: [] };
        try {
            horas = await api.llamar("reportes_horas_monitor", {});
            por_asignatura = await api.llamar("reportes_monitorias_asignatura", {});
            por_estado = await api.llamar("reportes_solicitudes_estado", {});
        } catch (error) {
            if (!contexto.vigente()) { return; }
            utilidades.mostrar_error(contenedor, error.message, function () {
                window.vistas_ucc.reportes(contenedor, contexto);
            });
            return;
        }
        if (!contexto.vigente()) { return; }
        utilidades.vaciar(contenedor);

        contenedor.append(utilidades.encabezado(
            "Reporte de monitorías",
            "Horas por monitor, monitorías por asignatura y solicitudes por estado. Datos en vivo desde la base de datos.",
            "Consulta y visualización"
        ));

        const formulario = utilidades.crear("form", "formulario_ucc barra_filtros");
        formulario.setAttribute("novalidate", "");
        const c_busqueda = utilidades.campo({
            id: "rep_busqueda", etiqueta: "Buscar", nombre: "q",
            placeholder_texto: "Monitor o asignatura..."
        });
        const asignaturas = Array.from(new Set((horas.filas || []).map(function (x) { return x.asignatura; })));
        const c_filtro = utilidades.campo({
            id: "rep_asignatura", etiqueta: "Asignatura", tipo: "select",
            opciones: asignaturas.map(function (a) { return { valor: a, texto: a }; })
        });
        formulario.append(c_busqueda.grupo, c_filtro.grupo);

        const zona_tabla = utilidades.crear("div");
        const zona_resumen = utilidades.crear("p", "texto_secundario texto_pequeno", "");

        function pintar() {
            const q = c_busqueda.control.value.trim().toLowerCase();
            const fa = c_filtro.control.value;
            const filas = (horas.filas || []).filter(function (x) {
                if (fa && x.asignatura !== fa) { return false; }
                if (q && (String(x.monitor) + " " + String(x.asignatura)).toLowerCase().indexOf(q) === -1) { return false; }
                return true;
            });
            utilidades.vaciar(zona_tabla);
            if (!filas.length) {
                zona_tabla.append(utilidades.estado_vacio("Sin resultados para los filtros.", "bi-search", true));
            } else {
                zona_tabla.append(utilidades.tabla([
                    { titulo: "Monitor", valor: "monitor" },
                    { titulo: "Asignatura", valor: "asignatura" },
                    { titulo: "Horas", valor: "horas" },
                    { titulo: "Informes", valor: "informes" }
                ], filas, "Horas por monitor"));
            }
            zona_resumen.textContent = filas.length + " de " + (horas.filas || []).length + " monitores.";
        }

        c_busqueda.control.addEventListener("input", pintar);
        c_filtro.control.addEventListener("change", pintar);
        formulario.addEventListener("submit", function (e) { e.preventDefault(); pintar(); });

        const btn_csv = utilidades.boton("Exportar CSV", "bi-send", "boton_secundario boton_pequeno", function () {
            descargar_csv("horas_por_monitor.csv",
                ["monitor", "asignatura", "horas", "informes"], horas.filas || []);
            utilidades.toast("CSV exportado.", "exito");
        });

        const btn_pdf = utilidades.boton("Exportar PDF", "bi-clipboard-check", "boton_claro boton_pequeno", function () {
            exportar_pdf(horas, por_asignatura, por_estado);
        });

        const zona_exportar = utilidades.crear("div", "grupo_botones");
        zona_exportar.append(btn_csv, btn_pdf);

        contenedor.append(formulario, zona_resumen, zona_tabla, zona_exportar);
        contenedor.append(utilidades.tabla([
            { titulo: "Asignatura", valor: "asignatura" },
            { titulo: "Total", valor: "total" },
            { titulo: "Programadas", valor: "programadas" },
            { titulo: "Realizadas", valor: "realizadas" }
        ], por_asignatura.filas || [], "Monitorías por asignatura"));
        contenedor.append(utilidades.tabla([
            { titulo: "Estado", valor: "estado" },
            { titulo: "Total", valor: "total" }
        ], por_estado.filas || [], "Solicitudes por estado"));
        pintar();
    };
})();

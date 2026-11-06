window.registro_ucc = (function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    // Debe mantenerse sincronizado con backend/app/catalogos.py (PROGRAMAS).
    const PROGRAMAS = [
        "Ingeniería de Software",
        "Ingeniería Industrial",
        "Ingeniería Civil",
        "Ingeniería Ambiental",
        "Psicología",
        "Administración de Empresas",
        "Derecho"
    ];

    const PATRON_CONTRASENA = "(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9]).{10,128}";

    let caja_login = null;
    let caja_registro = null;
    let formulario = null;
    let alerta = null;
    let boton_enviar = null;
    let enviando = false;

    function mostrar_alerta(mensaje, tipo) {
        if (!alerta) {
            return;
        }
        const nivel =
            tipo === "exito" ? "success" : tipo === "info" ? "info" : "danger";
        alerta.className = "alert alert-" + nivel;
        alerta.textContent = mensaje;
        alerta.classList.remove("d-none");
    }

    function ocultar_alerta() {
        if (!alerta) {
            return;
        }
        alerta.textContent = "";
        alerta.classList.add("d-none");
    }

    function mostrar_registro() {
        if (!caja_login || !caja_registro) {
            return;
        }
        caja_login.classList.add("d-none");
        caja_registro.classList.remove("d-none");
        ocultar_alerta();
        const primero = formulario
            ? formulario.querySelector("input, select")
            : null;
        if (primero) {
            primero.focus();
        }
    }

    function mostrar_login() {
        if (!caja_login || !caja_registro) {
            return;
        }
        caja_registro.classList.add("d-none");
        caja_login.classList.remove("d-none");
        ocultar_alerta();
        if (formulario) {
            formulario.classList.remove("was-validated");
            formulario.reset();
        }
        const correo_login = document.getElementById("correo_login");
        if (correo_login) {
            correo_login.focus();
        }
    }

    function construir_formulario() {
        const grupo_nombre = utilidades.campo({
            id: "nombre_registro",
            etiqueta: "Nombre completo",
            placeholder_texto: "Como aparece en su documento",
            maxlength: 160,
            required: true
        });

        const grupo_correo = utilidades.campo({
            id: "correo_registro",
            etiqueta: "Correo electrónico",
            tipo: "email",
            placeholder_texto: "nombre@ucc.edu.co",
            maxlength: 120,
            required: true
        });

        const grupo_telefono = utilidades.campo({
            id: "telefono_registro",
            etiqueta: "Teléfono de contacto (opcional)",
            tipo: "tel",
            placeholder_texto: "+57 300 000 0000",
            maxlength: 30
        });

        const grupo_programa = utilidades.campo({
            id: "programa_registro",
            etiqueta: "Programa académico",
            tipo: "select",
            opciones: PROGRAMAS,
            required: true
        });

        const grupo_semestre = utilidades.campo({
            id: "semestre_registro",
            etiqueta: "Semestre actual",
            tipo: "number",
            min: 1,
            max: 10,
            step: 1,
            required: true
        });

        const grupo_contrasena = utilidades.campo({
            id: "contrasena_registro",
            etiqueta: "Contraseña",
            tipo: "password",
            autocomplete: "new-password",
            minlength: 10,
            maxlength: 128,
            pattern: PATRON_CONTRASENA,
            title:
                "Use al menos 10 caracteres, una mayúscula, una minúscula y un número.",
            placeholder_texto: "Mínimo 10 caracteres",
            required: true
        });
        grupo_contrasena.control.insertAdjacentHTML(
            "afterend",
            "<div class=\"campo_ayuda\">Mínimo 10 caracteres, una mayúscula, una minúscula y un número.</div>"
        );

        const grupo_confirmacion = utilidades.campo({
            id: "confirmacion_registro",
            etiqueta: "Confirmar contraseña",
            tipo: "password",
            autocomplete: "new-password",
            minlength: 10,
            maxlength: 128,
            placeholder_texto: "Repita la contraseña",
            required: true
        });

        formulario.append(
            grupo_nombre.grupo,
            grupo_correo.grupo,
            grupo_telefono.grupo,
            grupo_programa.grupo,
            grupo_semestre.grupo,
            grupo_contrasena.grupo,
            grupo_confirmacion.grupo
        );

        boton_enviar = document.createElement("button");
        boton_enviar.type = "submit";
        boton_enviar.id = "boton_registro";
        boton_enviar.className = "btn boton_principal boton_ancho";
        boton_enviar.append(
            utilidades.icono("bi-person-plus"),
            document.createTextNode("Crear mi cuenta")
        );
        formulario.append(boton_enviar);

        return {
            nombre: grupo_nombre.control,
            correo: grupo_correo.control,
            telefono: grupo_telefono.control,
            programa: grupo_programa.control,
            semestre: grupo_semestre.control,
            contrasena: grupo_contrasena.control,
            confirmacion: grupo_confirmacion.control
        };
    }

    async function enviar(evento) {
        evento.preventDefault();
        if (enviando) {
            return;
        }
        ocultar_alerta();

        if (!formulario.checkValidity()) {
            formulario.classList.add("was-validated");
            formulario.reportValidity();
            return;
        }
        if (campos.contrasena.value !== campos.confirmacion.value) {
            formulario.classList.add("was-validated");
            mostrar_alerta(
                "La confirmación de la contraseña no coincide.",
                "error"
            );
            campos.confirmacion.focus();
            return;
        }

        enviando = true;
        utilidades.ocupar_boton(boton_enviar, true, "Creando cuenta...");
        try {
            const datos = await api.llamar("registrarse_estudiante", {
                nombre: campos.nombre.value.trim(),
                correo: campos.correo.value.trim(),
                telefono: campos.telefono.value.trim(),
                programa: campos.programa.value,
                semestre: campos.semestre.value,
                contrasena: campos.contrasena.value,
                confirmacion_contrasena: campos.confirmacion.value
            });
            if (typeof window.app_ucc.adoptar_sesion === "function") {
                window.app_ucc.adoptar_sesion(datos, datos.mensaje);
            } else {
                mostrar_alerta(
                    "Cuenta creada. Inicie sesión con sus datos.",
                    "exito"
                );
                mostrar_login();
            }
        } catch (error) {
            mostrar_alerta(error.message, "error");
            campos.contrasena.value = "";
            campos.confirmacion.value = "";
            campos.contrasena.focus();
        } finally {
            enviando = false;
            utilidades.ocupar_boton(boton_enviar, false);
            if (formulario) {
                formulario.classList.remove("was-validated");
            }
        }
    }

    function configurar_eventos(campos_entrada) {
        if (formulario) {
            formulario.addEventListener("submit", enviar);
        }
        const boton_ir = document.getElementById("boton_ir_registro");
        if (boton_ir) {
            boton_ir.addEventListener("click", mostrar_registro);
        }
        const boton_cancelar = document.getElementById(
            "boton_cancelar_registro"
        );
        if (boton_cancelar) {
            boton_cancelar.addEventListener("click", mostrar_login);
        }
        const boton_login_volver = document.getElementById(
            "boton_volver_login_registro"
        );
        if (boton_login_volver) {
            boton_login_volver.addEventListener("click", mostrar_login);
        }
    }

    let campos = null;

    function inicializar() {
        caja_login = document.getElementById("caja_login");
        caja_registro = document.getElementById("caja_registro");
        formulario = document.getElementById("formulario_registro");
        alerta = document.getElementById("alerta_registro");
        boton_enviar = document.getElementById("boton_registro");

        if (!caja_login || !caja_registro || !formulario) {
            return;
        }

        formulario.classList.add("formulario_ucc");
        campos = construir_formulario();
        configurar_eventos(campos);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializar);
    } else {
        inicializar();
    }

    return {
        mostrar_registro: mostrar_registro,
        mostrar_login: mostrar_login
    };
})();

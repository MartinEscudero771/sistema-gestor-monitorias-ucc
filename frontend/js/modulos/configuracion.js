window.vistas_ucc = window.vistas_ucc || {};

(function () {
    const utilidades = window.utilidades_ucc;
    const api = window.api_ucc;

    const TAMANO_LADO = 320;
    const CALIDAD_JPEG = 0.85;

    let foto_pendiente = "";
    let foto_actual = "";
    let tiene_foto_actual = false;
    let usuario_perfil = null;

    function crear_tarjeta(clases_titulo, titulo, etiqueta) {
        const tarjeta = utilidades.crear("section", "tarjeta_config");
        tarjeta.append(utilidades.crear("h3", clases_titulo, titulo));
        if (etiqueta) {
            tarjeta.firstChild.prepend(
                utilidades.crear("span", "etiqueta_vista", etiqueta)
            );
        }
        return tarjeta;
    }

    function pintar_avatar(predeterminado, foto) {
        const caja = utilidades.crear("div", "perfil_foto_caja");
        const marco = utilidades.crear(
            "div",
            "avatar_config" + (foto_pendiente || foto ? " avatar_con_foto" : "")
        );
        if (foto_pendiente || foto) {
            const imagen = document.createElement("img");
            imagen.src = foto_pendiente || foto;
            imagen.alt = "Foto de perfil propuesta";
            marco.append(imagen);
        } else {
            marco.textContent = utilidades.iniciales(predeterminado);
        }
        caja.append(
            marco,
            utilidades.crear(
                "p",
                "texto_secundario",
                foto_pendiente
                    ? "Foto lista para guardar. Conforme se guarde se verá en su panel."
                    : "Puede subir una imagen o tomarse una foto desde su cámara."
            )
        );
        return caja;
    }

    function recortar_cuadrado(fuente, ancho, alto) {
        const lienzo = document.createElement("canvas");
        lienzo.width = TAMANO_LADO;
        lienzo.height = TAMANO_LADO;
        const contexto = lienzo.getContext("2d");
        const lado = Math.min(ancho, alto);
        const origen_x = (ancho - lado) / 2;
        const origen_y = (alto - lado) / 2;
        contexto.drawImage(
            fuente,
            origen_x,
            origen_y,
            lado,
            lado,
            0,
            0,
            TAMANO_LADO,
            TAMANO_LADO
        );
        return lienzo.toDataURL("image/jpeg", CALIDAD_JPEG);
    }

    function procesar_archivo(archivo, al_obtener) {
        if (!archivo) {
            return;
        }
        if (!/^image\/(png|jpe?g)$/i.test(archivo.type)) {
            utilidades.toast("Elija una imagen PNG o JPEG.", "error");
            return;
        }
        const lector = new FileReader();
        lector.onload = function () {
            const imagen = new Image();
            imagen.onload = function () {
                if (typeof al_obtener === "function") {
                    al_obtener(
                        recortar_cuadrado(imagen, imagen.naturalWidth, imagen.naturalHeight)
                    );
                }
            };
            imagen.onerror = function () {
                utilidades.toast("La imagen no se pudo leer.", "error");
            };
            imagen.src = String(lector.result);
        };
        lector.onerror = function () {
            utilidades.toast("La imagen no se pudo leer.", "error");
        };
        lector.readAsDataURL(archivo);
    }

    function marcar_pendiente(dataurl, zona_acciones, refrescar) {
        foto_pendiente = dataurl;
        zona_acciones.classList.add("perfil_foto_pendiente");
        refrescar();
    }

    async function guardar_foto(dentro) {
        try {
            const respuesta = await api.llamar(
                "perfil_guardar_foto",
                { foto: foto_pendiente }
            );
            if (!dentro.vigente()) {
                return false;
            }
            foto_pendiente = "";
            foto_actual = respuesta.foto || "";
            tiene_foto_actual = !!foto_actual;
            utilidades.toast(respuesta.mensaje || "Foto guardada.", "exito");
            if (
                window.app_ucc.actualizar_identidad &&
                respuesta.foto !== undefined
            ) {
                window.app_ucc.actualizar_identidad({
                    foto: respuesta.foto || ""
                });
            }
            return true;
        } catch (error) {
            if (dentro.vigente()) {
                utilidades.toast(error.message, "error");
            }
            return false;
        }
    }

    async function quitar_foto_guardada(dentro) {
        try {
            const respuesta = await api.llamar("perfil_guardar_foto", {
                foto: ""
            });
            if (!dentro.vigente()) {
                return;
            }
            foto_pendiente = "";
            foto_actual = "";
            tiene_foto_actual = false;
            utilidades.toast(
                respuesta.mensaje || "Foto eliminada.",
                "exito"
            );
            if (window.app_ucc.actualizar_identidad) {
                window.app_ucc.actualizar_identidad({ foto: "" });
            }
            return true;
        } catch (error) {
            if (dentro.vigente()) {
                utilidades.toast(error.message, "error");
            }
            return false;
        }
    }

    function crear_modal_webcam(dentro, al_capturar) {
        const modal = utilidades.crear("div", "modal fade");
        modal.id = "modal_webcam_perfil";
        modal.tabIndex = -1;
        modal.setAttribute("aria-hidden", "true");
        modal.innerHTML =
            '<div class="modal-dialog modal-dialog-centered">' +
            '<div class="modal-content"><div class="modal-header"><div>' +
            '<p class="etiqueta_superior">Cámara</p>' +
            '<h2 class="modal-title">Tomar foto de perfil</h2></div>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>' +
            "</div><div class=\"modal-body webcam_cuerpo\">" +
            '<div class="webcam_marco"><video autoplay playsinline muted class="webcam_video"></video>' +
            '<p class="webcam_mensaje d-none"></p></div>' +
            '<p class="form-text">Al pulsar capturar se toma el cuadro central y se recorta a una imagen cuadrada.</p>' +
            "</div><div class=\"modal-footer webcam_acciones\">" +
            '<button type="button" class="btn boton_secundario" data-accion="cancelar">Cancelar</button>' +
            '<button type="button" class="btn boton_principal" data-accion="capturar">Capturar</button>' +
            "</div></div></div>";
        document.body.append(modal);

        const video = modal.querySelector("video");
        const mensaje = modal.querySelector(".webcam_mensaje");
        let flujo = null;
        let cerrado_por_exito = false;

        async function encender() {
            mensaje.textContent = "";
            mensaje.classList.add("d-none");
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                mensaje.textContent =
                    "Este navegador no permite usar la cámara aquí.";
                mensaje.classList.remove("d-none");
                return;
            }
            try {
                flujo = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 640 }, height: { ideal: 480 } },
                    audio: false
                });
                if (!dentro.vigente() || !modal.isConnected) {
                    apagar();
                    return;
                }
                video.srcObject = flujo;
            } catch (error) {
                mensaje.textContent =
                    "No fue posible acceder a la cámara. Revise los permisos del navegador.";
                mensaje.classList.remove("d-none");
            }
        }

        function apagar() {
            if (flujo) {
                flujo.getTracks().forEach(function (pista) {
                    pista.stop();
                });
                flujo = null;
            }
            video.srcObject = null;
        }

        modal.addEventListener("shown.bs.modal", encender);
        modal.addEventListener("hidden.bs.modal", function () {
            cerrado_por_exito = false;
            apagar();
        });

        modal.querySelector('[data-accion="cancelar"]').addEventListener(
            "click",
            function () {
                bootstrap.Modal.getOrCreateInstance(modal).hide();
            }
        );
        modal.querySelector('[data-accion="capturar"]').addEventListener(
            "click",
            function () {
                if (!video.videoWidth) {
                    mensaje.textContent =
                        "Espere a que la cámara esté lista antes de capturar.";
                    mensaje.classList.remove("d-none");
                    return;
                }
                const dataurl = recortar_cuadrado(
                    video,
                    video.videoWidth,
                    video.videoHeight
                );
                cerrado_por_exito = true;
                bootstrap.Modal.getOrCreateInstance(modal).hide();
                al_capturar(dataurl);
            }
        );

        const instancia = bootstrap.Modal.getOrCreateInstance(modal);
        instancia.show();
        return instancia;
    }

    async function guardar_datos(boton_guardar, dentro, campos_datos) {
        const valores = {};
        const nombre = campos_datos.nombre.control.value.trim();
        const telefono = campos_datos.telefono.control.value.trim();
        const correo_alterno = campos_datos.correo_alterno.control.value.trim();
        const previo = usuario_perfil || {};
        if (nombre && nombre !== (previo.nombre || "")) {
            valores.nombre = nombre;
        }
        if (telefono !== (previo.telefono || "")) {
            valores.telefono = telefono;
        }
        if (correo_alterno !== (previo.correo_alternativo || "")) {
            valores.correo_alternativo = correo_alterno;
        }
        if (!valores.nombre && !valores.telefono && !valores.correo_alternativo) {
            utilidades.toast(
                "No hay cambios que guardar. Modifique algún dato primero.",
                "info"
            );
            return;
        }
        utilidades.ocupar_boton(boton_guardar, true, "Guardando...");
        try {
            const respuesta = await api.llamar("perfil_guardar", valores);
            if (!dentro.vigente()) {
                return;
            }
            usuario_perfil = respuesta.usuario || usuario_perfil;
            utilidades.toast(
                respuesta.mensaje || "Datos actualizados.",
                "exito"
            );
            if (window.app_ucc.actualizar_identidad && usuario_perfil) {
                window.app_ucc.actualizar_identidad(usuario_perfil);
            }
        } catch (error) {
            if (dentro.vigente()) {
                utilidades.toast(error.message, "error");
            }
        } finally {
            utilidades.ocupar_boton(boton_guardar, false);
        }
    }

    function dibujar(contenedor, datos, contexto_vista) {
        usuario_perfil = datos.usuario || null;
        foto_pendiente = "";
        foto_actual = datos.foto || "";
        tiene_foto_actual = !!datos.tiene_foto;
        utilidades.vaciar(contenedor);

        contenedor.append(
            utilidades.encabezado(
                "Configuración",
                "configuracion",
                "Mi cuenta"
            )
        );

        const estructura = utilidades.crear("div", "config_grid");
        const datos_cuenta = utilidades.crear("div", "tarjeta_config");
        datos_cuenta.append(
            utilidades.crear("h3", "etiqueta_vista", "Datos de la cuenta")
        );
        datos_cuenta.append(
            utilidades.lista_datos([
                { etiqueta: "Rol", valor: datos.rol_texto },
                {
                    etiqueta: "Correo institucional",
                    valor: datos.correo_institucional
                },
                {
                    etiqueta: "Correo alterno",
                    valor: datos.correo_alternativo || "No registrado"
                },
                {
                    etiqueta: "Teléfono",
                    valor: datos.telefono || "No registrado"
                }
            ])
        );

        const tarjeta_foto = utilidades.crear("section", "tarjeta_config");
        tarjeta_foto.append(
            utilidades.crear(
                "h3",
                "etiqueta_vista",
                "Foto de perfil"
            ),
            utilidades.crear(
                "p",
                "texto_secundario",
                "Suba una imagen o tomese una foto con la camara; se guarda como imagen cuadrada de 320x320."
            )
        );
        const zona_acciones_foto = utilidades.crear("div", "perfil_foto_zona");

        const entrada_archivo = document.createElement("input");
        entrada_archivo.type = "file";
        entrada_archivo.accept = "image/png,image/jpeg";
        entrada_archivo.className = "d-none";
        entrada_archivo.id = "entrada_foto_perfil";

        function refrescar_vista_foto() {
            const caja = pintar_avatar(datos.usuario.nombre, foto_actual);
            utilidades.vaciar(zona_acciones_foto);
            zona_acciones_foto.append(caja);

            const acciones = utilidades.crear(
                "div",
                "acciones_formulario columna"
            );
            const boton_archivo = utilidades.boton(
                "Subir imagen",
                "bi-image-up",
                "boton_claro boton_pequeno",
                function () {
                    entrada_archivo.click();
                }
            );
            const boton_camara = utilidades.boton(
                "Tomar con la cámara",
                "bi-camera",
                "boton_claro boton_pequeno",
                function () {
                    crear_modal_webcam(contexto_vista, function (dataurl) {
                        marcar_pendiente(dataurl, zona_acciones_foto, refrescar_vista_foto);
                    });
                }
            );
            acciones.append(boton_archivo, boton_camara);

            if (foto_pendiente) {
                const barra_pendiente = utilidades.crear(
                    "div",
                    "acciones_formulario perfil_pendiente"
                );
                const boton_guardar_foto = utilidades.boton(
                    "Guardar foto",
                    "bi-check2-circle",
                    "boton_exito boton_pequeno"
                );
                const boton_descartar = utilidades.boton(
                    "Descartar",
                    "bi-x-lg",
                    "boton_secundario boton_pequeno",
                    function () {
                        foto_pendiente = "";
                        refrescar_vista_foto();
                    }
                );
                boton_guardar_foto.addEventListener("click", async function () {
                    utilidades.ocupar_boton(boton_guardar_foto, true, "Guardando...");
                    const ok = await guardar_foto(contexto_vista);
                    utilidades.ocupar_boton(boton_guardar_foto, false);
                    if (ok) {
                        refrescar_vista_foto();
                    }
                });
                barra_pendiente.append(boton_guardar_foto, boton_descartar);
                acciones.append(barra_pendiente);
            } else if (tiene_foto_actual) {
                const boton_quitar = utilidades.boton(
                    "Quitar foto",
                    "bi-x-lg",
                    "boton_secundario boton_pequeno",
                    async function () {
                        utilidades.ocupar_boton(boton_quitar, true, "Quitando...");
                        const ok = await quitar_foto_guardada(contexto_vista);
                        utilidades.ocupar_boton(boton_quitar, false);
                        if (ok) {
                            refrescar_vista_foto();
                        }
                    }
                );
                acciones.append(boton_quitar);
            }
            zona_acciones_foto.append(acciones);
        }

        refrescar_vista_foto();
        tarjeta_foto.append(zona_acciones_foto);

        const tarjeta_contacto = utilidades.crear("section", "tarjeta_config");
        tarjeta_contacto.append(
            utilidades.crear("h3", "etiqueta_vista", "Datos de contacto")
        );
        const campos_datos = {
            nombre: utilidades.campo({
                id: "perfil_nombre",
                etiqueta: "Nombre",
                valor: datos.usuario.nombre,
                maxlength: 160,
                minlength: 5,
                required: true
            }),
            telefono: utilidades.campo({
                id: "perfil_telefono",
                etiqueta: "Teléfono",
                tipo: "tel",
                valor: datos.telefono || "",
                maxlength: 30,
                placeholder_texto: "+57 300 000 0000"
            }),
            correo_alterno: utilidades.campo({
                id: "perfil_correo_alterno",
                etiqueta: "Correo alterno (no institucional)",
                tipo: "email",
                valor: datos.correo_alternativo || "",
                maxlength: 160,
                placeholder_texto: "personal@correo.com",
                ayuda:
                    "Su correo institucional (" +
                    datos.correo_institucional +
                    ") no se puede cambiar ni repetir aquí."
            })
        };
        const boton_guardar_datos = utilidades.boton(
            "Guardar cambios",
            "bi-check2-circle",
            "boton_principal"
        );
        boton_guardar_datos.addEventListener("click", function () {
            guardar_datos(boton_guardar_datos, contexto_vista, campos_datos);
        });
        tarjeta_contacto.append(
            campos_datos.nombre.grupo,
            campos_datos.telefono.grupo,
            campos_datos.correo_alterno.grupo,
            boton_guardar_datos
        );

        contenedor.append(estructura);
        estructura.append(tarjeta_contacto, tarjeta_foto, datos_cuenta);
        contenedor.append(entrada_archivo);

        entrada_archivo.addEventListener("change", function () {
            const archivo = entrada_archivo.files
                && entrada_archivo.files[0];
            procesar_archivo(archivo, function (dataurl) {
                entrada_archivo.value = "";
                marcar_pendiente(dataurl, zona_acciones_foto, refrescar_vista_foto);
            });
        });
    }

    window.vistas_ucc.configuracion = async function (contenedor, contexto) {
        const dentro = contexto;
        utilidades.cargar_vista(contenedor, "perfil_obtener", dentro, function (
            datos
        ) {
            dibujar(contenedor, datos, dentro);
        });
    };
})();

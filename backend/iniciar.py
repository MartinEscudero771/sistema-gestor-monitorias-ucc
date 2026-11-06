import uvicorn

from app.configuracion import HOST_ESCUCHA, PUERTO_SERVIDOR, URL_SERVIDOR


if __name__ == "__main__":
    print("")
    print("Sistema de Gestor de Monitorías Académicas UCC")
    print(f"Abra {URL_SERVIDOR}")
    print("Presione Ctrl+C para detener el servidor.")
    print("")
    uvicorn.run(
        "app.principal:aplicacion",
        host=HOST_ESCUCHA,
        port=PUERTO_SERVIDOR,
        reload=False,
        log_level="info",
    )

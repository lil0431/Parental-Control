from el_control2 import *


def windowStart():
    # Crea la ventana principal
    window = tk.Tk()
    window.title("Control Parental")
    window.geometry("600x400")  # Tamaño de la ventana

    # Define una imagen de ejemplo
    # La imagen debe estar en el mismo directorio que el script o proporcionar la ruta completa.
    try:
        imagen = PhotoImage(file="logo.png")  # Reemplaza con el nombre de tu archivo de imagen
    except Exception as e:
        print("Error al cargar la imagen:", e)
        imagen = None

    # Usa grid para organizar los elementos
    window.columnconfigure(0, weight=1)  # Columna izquierda
    window.columnconfigure(1, weight=1)  # Columna central
    window.columnconfigure(2, weight=1)  # Columna derecha

    # Columna de botones izquierda
    boton_izq1 = tk.Button(window, text="Start", command=start) #command indica el metodo que hay que utilizar
    boton_izq1.grid(row=0, column=0, padx=10, pady=10)

    boton_izq2 = tk.Button(window, text="Exportar fichero", command=lambda: password_csv(report_file, report_file2, password))
    boton_izq2.grid(row=1, column=0, padx=10, pady=10)

    boton_izq3 = tk.Button(window, text="login", command=login)
    boton_izq3.grid(row=2, column=0, padx=10, pady=10)

    # Columna de botones derecha
    boton_der1 = tk.Button(window, text="Stop",command=stop)
    boton_der1.grid(row=0, column=2, padx=10, pady=10)

    boton_der2 = tk.Button(window, text="Añadir palabra", command=add_blocked_keyword)
    boton_der2.grid(row=1, column=2, padx=10, pady=10)


    # Imagen en el centro
    if imagen:
        etiqueta_imagen = tk.Label(window, image=imagen)
        etiqueta_imagen.grid(row=0, column=1, rowspan=2, padx=10, pady=10)
    else:
        etiqueta_imagen = tk.Label(window, text="Imagen no encontrada")
        etiqueta_imagen.grid(row=0, column=1, rowspan=2, padx=10, pady=10)
    # Inicia el bucle principal de la ventana
    window.mainloop()



windowStart()

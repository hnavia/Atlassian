import csv

# --- CONFIGURACIÓN ---
INPUT_FILE = r'D:\Accounts\Rice\CSV\Validación\duplicates.csv'
OUTPUT_FILE = r'D:\Accounts\Rice\CSV\Validación\duplicates_limpio.csv'
DELIMITADOR = ';'

# Coordenadas (0 = primera columna)
COL_USERNAME = 0     # columna username
COL_EMAIL = 1        # columna email
COL_TYPE = 2         # columna type ("Cloud" o "DC")

# -------------------------------------------------------------

def limpiar_duplicados_prioridad_cloud_coords(archivo_entrada, archivo_salida,
                                              delimitador, col_user, col_email, col_type):
    """
    Elimina duplicados basados en (username + email), usando coordenadas de columna.
    Prioriza Cloud sobre DC cuando ambos existen.
    """

    filas_por_clave = {}
    filas_totales = 0
    duplicados_descartados = 0

    try:
        with open(archivo_entrada, mode='r', encoding='utf-8', newline='') as f_in:
            lector = csv.reader(f_in, delimiter=delimitador)

            # Leer encabezado tal cual para mantenerlo en el archivo final
            encabezado = next(lector)

            for fila in lector:
                filas_totales += 1

                username = fila[col_user].strip().lower()
                email = fila[col_email].strip().lower()
                tipo = fila[col_type].strip()

                clave = (username, email)

                if clave not in filas_por_clave:
                    filas_por_clave[clave] = fila  # primera aparición
                else:
                    fila_existente = filas_por_clave[clave]
                    tipo_existente = fila_existente[col_type]

                    # --- LÓGICA DE PRIORIDAD ---
                    if tipo_existente == "DC" and tipo == "Cloud":
                        # reemplazar DC por Cloud
                        filas_por_clave[clave] = fila
                        duplicados_descartados += 1
                    else:
                        # si el existente ya es Cloud, o si ambos son DC → descartar fila actual
                        duplicados_descartados += 1

        # --- GUARDAR RESULTADO ---
        with open(archivo_salida, mode='w', encoding='utf-8', newline='') as f_out:
            escritor = csv.writer(f_out, delimiter=delimitador)

            escritor.writerow(encabezado)
            for fila in filas_por_clave.values():
                escritor.writerow(fila)

        print("-" * 60)
        print("✅ Proceso terminado correctamente")
        print("-" * 60)
        print(f"📄 Filas leídas: {filas_totales}")
        print(f"🗑️  Duplicados descartados (incluye DC reemplazado por Cloud): {duplicados_descartados}")
        print(f"💾 Filas finales: {len(filas_por_clave)}")
        print(f"👉 Archivo guardado como: {archivo_salida}")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")


# --- EJECUCIÓN ---
if __name__ == "__main__":
    limpiar_duplicados_prioridad_cloud_coords(
        INPUT_FILE, OUTPUT_FILE, DELIMITADOR,
        COL_USERNAME, COL_EMAIL, COL_TYPE
    )

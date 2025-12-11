import pandas as pd

# === CONFIGURACIÓN ===
archivo_cloud = r'D:\Accounts\Rice\CSV\Validación\2025-11-13 Atlassian Cloud.csv'
archivo_dc     = r'D:\Accounts\Rice\CSV\Validación\duplicates_limpio.csv'
salida         = r'D:\Accounts\Rice\CSV\Validación\resultado_final3.csv'

delimitador = ';'
encoding    = 'latin1'

# Coordenadas archivo DC (0 = primera columna)
COL_USER_DC  = 0
COL_EMAIL_DC = 1
COL_TYPE_DC  = 2

# === CARGA (robusta) ===
df_cloud = pd.read_csv(archivo_cloud, sep=delimitador, encoding=encoding, engine='python')
df_dc    = pd.read_csv(archivo_dc,    sep=delimitador, encoding=encoding, engine='python')

# === RENOMBRAR COLUMNAS POR ORDEN (archivo Cloud) ===
df_cloud.columns = ['Name', 'Email', 'Username', 'Atlassian_ID', 'Status']

# === RENOMBRAR DC USANDO COORDENADAS ===
df_dc = df_dc.rename(columns={
    df_dc.columns[COL_USER_DC]:  'user_name',
    df_dc.columns[COL_EMAIL_DC]: 'email_address',
    df_dc.columns[COL_TYPE_DC]:  'type'
})

# Normalizar datos
df_dc['user_name']     = df_dc['user_name'].astype(str).str.strip().str.lower()
df_dc['email_address'] = df_dc['email_address'].astype(str).str.strip().str.lower()
df_dc['type']          = df_dc['type'].astype(str).str.strip()

# === AGRUPAR CORREOS POR USUARIO (generando listas de emails Cloud y DC por separado) ===
dc_grouped = (
    df_dc.groupby('user_name', observed=True, sort=False)
         .apply(
             lambda g: pd.Series({
                 'cloud_emails': g.loc[g['type'] == 'Cloud', 'email_address'].tolist(),
                 'dc_emails':    g.loc[g['type'] == 'DC',    'email_address'].tolist()
             }),
             include_groups=False  # evita el FutureWarning
         )
         .reset_index()
)

# === MERGE POR USERNAME ===
df = df_cloud.merge(dc_grouped, how='left',
                    left_on='Username', right_on='user_name')

# === CREAR COLUMNAS CLOUD EMAIL Y DC EMAIL ===
def list_or_empty(x):
    return x if isinstance(x, list) else []

df['cloud_emails'] = df['cloud_emails'].apply(list_or_empty)
df['dc_emails']    = df['dc_emails'].apply(list_or_empty)

# Expandir Cloud Email
max_cloud = df['cloud_emails'].str.len().max()

for i in range(max_cloud):
    df[f'Cloud email {i+1}'] = df['cloud_emails'].apply(lambda x: x[i] if len(x) > i else '')

# Expandir DC Email
max_dc = df['dc_emails'].str.len().max()

for i in range(max_dc):
    df[f'DC email {i+1}'] = df['dc_emails'].apply(lambda x: x[i] if len(x) > i else '')

# === INDICADOR EXISTS ===
df['Exists'] = df.apply(
    lambda row: 'Yes' if (len(row['cloud_emails']) + len(row['dc_emails'])) > 0 else 'No',
    axis=1
)

# === LIMPIAR COLUMNAS AUXILIARES ===
df = df.drop(columns=['user_name', 'cloud_emails', 'dc_emails'])

# === EXPORTAR ===
df.to_csv(salida, sep=delimitador, encoding=encoding, index=False)

print("Archivo generado:", salida)

# === RESUMEN FINAL ===
total_registros = len(df)
coinciden        = df['Exists'].value_counts().get('Yes', 0)
no_coinciden     = df['Exists'].value_counts().get('No', 0)

# Contar columnas que representan correos expandidos
total_cloud_cols = len([c for c in df.columns if c.startswith('Cloud email')])
total_dc_cols    = len([c for c in df.columns if c.startswith('DC email')])

print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"Total users processed        : {total_registros}")
print(f"Users with matches (Yes)     : {coinciden}")
print(f"Users without matches (No)   : {no_coinciden}")
print("")
print(f"Cloud email columns created  : {total_cloud_cols}")
print(f"DC email columns created     : {total_dc_cols}")
print("="*60)


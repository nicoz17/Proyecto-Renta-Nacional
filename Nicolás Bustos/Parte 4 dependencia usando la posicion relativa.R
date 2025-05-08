library(dplyr)
library(readxl)

# Cargar datos de COTIZACIONES_202404
COTIZACIONES_202404 <- read_excel("D:/descargas/clases/6 año 1 semestre/Capstone Mate/COTIZACIONES_202404.xlsx")

# Crear ids_con_aceptada
ids_con_aceptada <- COTIZACIONES_202404 %>%
  filter(ACEPTADA == 1) %>%
  pull(COTIZANTE) %>%
  unique()

# Convertir la variable ACEPTADA de -1 a 1
COTIZACIONES_202404 <- COTIZACIONES_202404 %>%
  mutate(ACEPTADA = ifelse(ACEPTADA == -1, 1, ACEPTADA))

# Filtrar los datos según condiciones específicas
datos_filtrados <- COTIZACIONES_202404 %>%
  filter((COTIZANTE %in% ids_con_aceptada & ACEPTADA == 1 & TIPO_RENTA == "I" & MODALIDAD_RENTA == "G") |
           (!(COTIZANTE %in% ids_con_aceptada) & TIPO_RENTA == "I" & MODALIDAD_RENTA == "G"))

# Selección de columnas numéricas y eliminación de columnas constantes
numericas <- datos_filtrados %>%
  select(where(is.numeric))

# Eliminar columnas con desviación estándar cero
numericas_sin_constantes <- numericas %>%
  select(where(~sd(., na.rm = TRUE) != 0))

# Cargar datos de SC_COTIZACIONES
SC_COTIZACIONES <- read_excel("D:/descargas/clases/6 año 1 semestre/Capstone Mate/SC_COTIZACIONES_202404.xlsx")

# Paso 1: Realizar el left_join utilizando tanto COTIZANTE como COTIZACION
datos_filtrados_con_posicion <- datos_filtrados %>%
  left_join(SC_COTIZACIONES %>% select(COTIZANTE, COTIZACION, POSICION_RELATIVA),
            by = c("COTIZANTE", "COTIZACION"))

# Paso 2: Asegurar que POSICION_RELATIVA sea numérica
datos_filtrados_con_posicion <- datos_filtrados_con_posicion %>%
  mutate(POSICION_RELATIVA = as.numeric(POSICION_RELATIVA))

# Paso 3: Seleccionar solo columnas numéricas
numericas <- datos_filtrados_con_posicion %>%
  select(where(is.numeric))

# Guardar la variable respuesta
ACEPTADA_var <- numericas$ACEPTADA

# Paso 4: Eliminar columnas constantes
numericas_sin_constantes <- numericas %>%
  select(where(~sd(., na.rm = TRUE) != 0))

# Paso 5: Verificar si POSICION_RELATIVA sigue presente, si no, la reincorporamos
if (!"POSICION_RELATIVA" %in% colnames(numericas_sin_constantes)) {
  numericas_sin_constantes <- bind_cols(numericas_sin_constantes,
                                        POSICION_RELATIVA = numericas$POSICION_RELATIVA)
  cat("POSICION_RELATIVA fue agregada manualmente porque fue eliminada en el filtrado.\n")
}

# Paso 6: Asegurar que ACEPTADA esté presente
if (!"ACEPTADA" %in% colnames(numericas_sin_constantes)) {
  numericas_sin_constantes <- numericas_sin_constantes %>%
    mutate(ACEPTADA = ACEPTADA_var)
}

# Paso 7: Eliminar filas con NA
datos_modelo <- na.omit(numericas_sin_constantes)

# Paso 8: Modelo de regresión logística
modelo_logistico <- glm(ACEPTADA ~ ., data = datos_modelo, family = binomial)

# Paso 9: Mostrar resultados
summary(modelo_logistico)




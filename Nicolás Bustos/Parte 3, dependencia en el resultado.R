# Convertir la variable ACEPTADA de -1 a 1
COTIZACIONES_202404 <- COTIZACIONES_202404 %>%
  mutate(ACEPTADA = ifelse(ACEPTADA == -1, 1, ACEPTADA))

# Repetir los pasos de filtrado y selección de variables numéricas
datos_filtrados <- COTIZACIONES_202404 %>%
  filter((COTIZANTE %in% ids_con_aceptada & ACEPTADA == 1 & TIPO_RENTA == "I" & MODALIDAD_RENTA == "G") |
           (!(COTIZANTE %in% ids_con_aceptada) & TIPO_RENTA == "I" & MODALIDAD_RENTA == "G"))

# Selección de columnas numéricas y eliminación de columnas constantes
numericas <- datos_filtrados %>%
  select(where(is.numeric))

numericas_sin_constantes <- numericas %>%
  select(where(~sd(., na.rm = TRUE) != 0))  # Seleccionamos solo columnas con desviación estándar distinta de cero

# Modelo de regresión logística
modelo_logistico <- glm(ACEPTADA ~ ., data = numericas_sin_constantes, family = binomial)

# Ver el resumen del modelo
summary(modelo_logistico)

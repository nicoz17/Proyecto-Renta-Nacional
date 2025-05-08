SCOMP_MERCADO_2023 <- read_excel("D:/descargas/clases/6 año 1 semestre/Capstone Mate/SCOMP_MERCADO_2023.xlsx",sheet = "CES ING POR DIA", col_types = c("date", "text", "text", "numeric"))
SCOMP_MERCADO_2024 <- read_excel("D:/descargas/clases/6 año 1 semestre/Capstone Mate/SCOMP_MERCADO_2024.xlsx",sheet = "CES ING POR DIA", col_types = c("date", "text", "text", "numeric"))

CES2023 = SCOMP_MERCADO_2023$CES.Ingresados
CES2024 = SCOMP_MERCADO_2024$CES.Ingresados

Fechas2023 = SCOMP_MERCADO_2023$Fecha.Recepcion.CES
Fechas2024 = SCOMP_MERCADO_2024$Fecha.Recepcion.CES

#unimos CES y fechas de 2023 y 2024
CES = c(CES2023, CES2024)
Fechas = c(Fechas2023, Fechas2024)

# Paso 1: Asegurarse de que las fechas estén en formato Date
Fechas <- as.Date(Fechas)  # Si están en POSIXct, esto elimina la hora

# Paso 2: Agrupar por fecha y sumar los valores
serie_diaria <- aggregate(CES, by = list(Fecha = Fechas), FUN = sum)
colnames(serie_diaria) <- c("Fecha", "Suma_CES")

# Paso 3: Crear una secuencia completa de fechas
fechas_completas <- seq(min(serie_diaria$Fecha), max(serie_diaria$Fecha), by = "day")

# Paso 4: Unir con tus datos agregados (completando días faltantes con NA)
serie_completa <- merge(data.frame(Fecha = fechas_completas),
                        serie_diaria,
                        by = "Fecha", all.x = TRUE)

# Paso 5: Rellenar NA con 0 (opcional)
serie_completa$Suma_CES[is.na(serie_completa$Suma_CES)] <- 0

# Paso 6: Convertir a objeto ts
ts_diaria <- ts(serie_completa$Suma_CES,
                start = c(as.numeric(format(min(serie_completa$Fecha), "%Y")),
                          as.numeric(format(min(serie_completa$Fecha), "%j"))),
                frequency = 365)

# Paso 7 (opcional): graficar
plot(ts_diaria, type = "l", col = "blue",
     main = "Serie de Tiempo Diaria de CES",
     xlab = "Día del año", ylab = "Suma CES")
abline(h = 0, col = "red", lty = 2)
abline(h = mean(ts_diaria), col = "green", lty = 2)
#leyenda
legend("topright", legend = c("Serie de Tiempo", "Media", "Cero"),
       col = c("blue", "green", "red"), lty = c(1, 2, 2), bty = "n")
# ACF y PACF
par(mfrow = c(1, 1))
acf(ts_diaria, main = "ACF de la serie de CES", ylim = c(-1, 1), lag.max = 30)
pacf(ts_diaria, main = "PACF de la serie de CES", ylim = c(-1, 1), lag.max = 30)

     


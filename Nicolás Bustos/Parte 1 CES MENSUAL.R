CES <- c(10608, 9578, 11479, 9638, 9518, 8816,
         11016, 9991, 7710, 10055, 10261, 9316,
         11658, 10046, 10778, 11071, 9129, 8380,
         9909, 9478, 9070, 11139, 9007, 8922)

# Generar vector de fechas mensuales
meses <- seq(from = as.Date("2023-01-01"), to = as.Date("2024-12-01"), by = "month")

# Convertir las fechas a nombres de mes y año abreviado
etiquetas <- format(meses, "%b %Y")

# Mostrar solo etiquetas mes por medio
etiquetas[seq(2, length(etiquetas), by = 2)] <- ""

# Gráfico
barplot(CES, names.arg = etiquetas, col = "skyblue", main = "Número de Cotizaciones 2023-2024", 
        ylab = "Cantidad", ylim = c(0, 15000), las = 2, cex.names = 0.8)
abline(h = seq(0, 15000, by = 1000), col = "gray", lty = 2)
abline(h = mean(CES), col = "red", lwd = 2)

# Leyenda
legend("topright", legend = c("Media"), col = "red", lwd = 2, bty = "n")



#regresion lineal
modelo <- lm(CES ~ meses)
summary(modelo)
# grafico de la regresion lineal
plot(meses, CES, type = "p", col = "skyblue", pch = 16,
     xlab = "Meses", ylab = "Cotizaciones", 
     main = "Tendencia de Cotizaciones 2023-2024")

# Prueba de normalidad de Shapiro-Wilk
shapiro.test(CES)

# qqnorm
qqnorm(CES)
qqline(CES, col = "red")

sd(CES)
mean(CES)

# Histograma
hist(CES, 
     col = "lightblue", 
     main = "Distribución de las Cotizaciones", 
     xlab = "Cotizaciones", 
     ylab = "Frecuencia", 
     breaks = 13)


# Línea de tendencia
plot(meses, CES, type = "o", col = "skyblue", pch = 16,
     xlab = "", ylab = "Cotizaciones", 
     main = "Tendencia de Cotizaciones 2023-2024", ylim = c(6000, 13000),
     xaxt = "n")  # Desactiva el eje X automático

# Crear etiquetas mes por medio
etiquetas <- format(meses, "%b %Y")
posiciones <- seq(1, length(meses), by = 2)  # Índices de los meses a etiquetar

# Agregar eje X personalizado
axis(1, at = meses[posiciones], labels = etiquetas[posiciones], las = 2, cex.axis = 0.8)

# Línea de tendencia
abline(lm(CES ~ as.numeric(meses)), col = "red", lwd = 2)


summary(lm(CES ~ as.numeric(meses)))




# revisamos como serie de tiempo si hay patron estacional
# Convertir el vector CES a una serie de tiempo
CES_ts <- ts(CES, start = c(2023, 1), frequency = 12)
# Graficar la serie de tiempo
plot(CES_ts, 
     main = "Serie de Tiempo de Cotizaciones", 
     ylab = "Cotizaciones", 
     xlab = "Meses", 
     col = "skyblue", 
     lwd = 2)
# grafico acf y pacf
par(mfrow = c(1, 2))
acf(CES_ts, main = "ACF de Cotizaciones", ylim = c(-1, 1))
pacf(CES_ts, main = "PACF de Cotizaciones", ylim = c(-1, 1))

sum(CES)

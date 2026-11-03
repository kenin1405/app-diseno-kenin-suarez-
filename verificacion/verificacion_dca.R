# Carga el archivo CSV alternativo desde data, usando como referencia la carpeta verificacion.
datos <- read.csv("../data/dca_mi_variante.csv", stringsAsFactors = FALSE) # Lee los datos del ensayo.
# Ajusta el análisis de varianza de un factor para comparar los secadores.
modelo <- aov(humedad ~ factor(secador), data = datos) # Usa secador como factor y humedad como respuesta.
# Imprime la tabla ANOVA para revisar el efecto de los secadores.
print(summary(modelo)) # Muestra grados de libertad, cuadrados medios, estadístico F y p-valor.
# Calcula y muestra la media de humedad para cada secador.
medias <- aggregate(humedad ~ secador, data = datos, FUN = mean) # Agrupa por secador y calcula la media.
print(medias) # Imprime las medias calculadas por tratamiento.
# Extrae el cuadrado medio del error de la tabla ANOVA.
tabla_anova <- summary(modelo)[[1]] # Guarda la tabla ANOVA como matriz para acceder a sus componentes.
cme <- tabla_anova["Residuals", "Mean Sq"] # Obtiene el cuadrado medio del error residual.
# Calcula la media general de la humedad observada.
media_general <- mean(datos$humedad) # Promedia todas las observaciones, sin separar por secador.
# Calcula el coeficiente de variación como raíz del CME dividida por la media general, por 100.
cv <- sqrt(cme) / media_general * 100 # Aplica CV = sqrt(CME) / media general * 100.
cat(sprintf("Coeficiente de variación: %.4f%%\n", cv)) # Imprime el CV con cuatro decimales y el símbolo porcentual.
# Imprime las comparaciones múltiples de Tukey para los niveles de secador.
print(TukeyHSD(modelo)) # Muestra diferencias de medias, intervalos y valores p ajustados.

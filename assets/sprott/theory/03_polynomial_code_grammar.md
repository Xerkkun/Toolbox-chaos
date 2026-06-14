# 03 Polynomial Code Grammar

Las letras `A-X` representan familias polinomiales. Cada grupo de cuatro letras
mantiene dimension y tipo, y cambia el orden polinomial de 2 a 5.

El numero de monomios de grado total menor o igual que `O` en dimension `D` es
`comb(D + O, O)`. Como hay una ecuacion por variable, el numero de coeficientes
es `D * comb(D + O, O)`.

Los coeficientes educativos se leen con `(ord(letter)-77)/10`: `M` es cero,
letras anteriores a `M` son negativas y letras posteriores son positivas.
Familias especiales `Y-Z` quedan documentadas como pendientes.

"""Cortes de IMC por edad y sexo para 5 a 17 años (referencia de crecimiento de la OMS, 2007).

Fuente: OMS, «Growth reference data for 5-19 years», IMC para la edad, tablas expandidas de
puntuaciones z (bmi-boys-z-who-2007-exp.xlsx y bmi-girls-z-who-2007-exp.xlsx), publicadas en
https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age

Cada fila es la edad en años cumplidos y trae el IMC (kg/m²) de las puntuaciones z
(-3, -2, +1, +2) a la mitad de ese año (edad en meses = años x 12 + 6). El sistema solo guarda la
edad en años, por eso se toma el punto medio del año.
"""

# sexo -> edad en años -> (z-3, z-2, z+1, z+2)
CUTOFFS: dict[str, dict[int, tuple[float, float, float, float]]] = {
    "M": {
        5: (11.742, 12.718, 16.923, 19.009),
        6: (11.725, 12.704, 17.131, 19.482),
        7: (11.803, 12.795, 17.488, 20.149),
        8: (11.98, 13.001, 18.012, 21.019),
        9: (12.231, 13.296, 18.666, 22.031),
        10: (12.542, 13.666, 19.429, 23.134),
        11: (12.931, 14.129, 20.32, 24.338),
        12: (13.379, 14.663, 21.305, 25.596),
        13: (13.824, 15.2, 22.279, 26.786),
        14: (14.207, 15.674, 23.145, 27.804),
        15: (14.488, 16.037, 23.832, 28.58),
        16: (14.656, 16.277, 24.324, 29.105),
        17: (14.725, 16.409, 24.649, 29.418),
    },
    "F": {
        5: (12.115, 13.021, 16.676, 18.35),
        6: (12.189, 13.086, 16.888, 18.745),
        7: (12.319, 13.221, 17.231, 19.328),
        8: (12.475, 13.392, 17.663, 20.056),
        9: (12.661, 13.603, 18.179, 20.916),
        10: (12.905, 13.886, 18.808, 21.914),
        11: (13.213, 14.245, 19.542, 23.009),
        12: (13.588, 14.684, 20.375, 24.165),
        13: (14.029, 15.202, 21.298, 25.347),
        14: (14.489, 15.747, 22.235, 26.462),
        15: (14.916, 16.265, 23.116, 27.441),
        16: (15.285, 16.728, 23.91, 28.271),
        17: (15.577, 17.118, 24.603, 28.954),
    },
}

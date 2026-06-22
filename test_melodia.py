from melodia import (analizar, EJEMPLO, ErrorLexico, ErrorSintactico, ErrorSemantico)
import unittest

class Validas(unittest.TestCase):
    def test_ejemplo_completo(self):
        r = analizar(EJEMPLO)
        # 1+1+2 + 1(acorde) + 1(silencio) + 2*(0.5+0.5) = 8 negras
        self.assertEqual(r['beats'], 8.0)
        self.assertEqual(r['tempo'], 120)
        self.assertAlmostEqual(r['segundos'], 4.0)

    def test_tempo_por_defecto(self):
        r = analizar('Cancion "x" { Nota do negra; }')
        self.assertEqual(r['tempo'], 100)

    def test_duraciones(self):
        r = analizar('Cancion "x" { Nota do redonda; Silencio corchea; }')
        self.assertEqual(r['beats'], 4.5)

    def test_repetir_anidado(self):
        r = analizar('Cancion "x" { Repetir 3 { Repetir 2 { Nota do negra; }; }; }')
        self.assertEqual(r['beats'], 6.0)

class Lexicos(unittest.TestCase):
    def test_caracter_invalido(self):
        with self.assertRaises(ErrorLexico):
            analizar('Cancion "x" { Nota do @; }')

class Sintacticos(unittest.TestCase):
    def test_falta_punto_y_coma(self):
        with self.assertRaises(ErrorSintactico):
            analizar('Cancion "x" { Nota do negra }')

    def test_falta_llave(self):
        with self.assertRaises(ErrorSintactico):
            analizar('Cancion "x" Nota do negra;')

    def test_cancion_vacia(self):
        # se exige al menos una sentencia (sentencias : sentencia ...)
        with self.assertRaises(ErrorSintactico):
            analizar('Cancion "x" { }')

class Semanticos(unittest.TestCase):
    def test_nota_invalida(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Nota xyz negra; }')

    def test_duracion_invalida(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Nota do larga; }')

    def test_tempo_duplicado(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Tempo 90; Tempo 120; Nota do negra; }')

    def test_tempo_no_positivo(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Tempo 0; Nota do negra; }')

    def test_repetir_cero(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Repetir 0 { Nota do negra; }; }')

    def test_acorde_una_nota(self):
        with self.assertRaises(ErrorSemantico):
            analizar('Cancion "x" { Acorde do; }')

if __name__ == '__main__':
    unittest.main()
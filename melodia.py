"""Melodia: lenguaje musical. PLY (lex + yacc)."""
import ply.lex as lex
import ply.yacc as yacc

# ===================== ERRORES =====================
class ErrorLexico(Exception):
    pass

class ErrorSintactico(Exception):
    pass

class ErrorSemantico(Exception):
    pass

# ===================== AST =====================
class Cancion:
    def __init__(self, nombre, sentencias):
        self.nombre = nombre
        self.sentencias = sentencias

class Tempo:
    def __init__(self, valor, linea):
        self.valor, self.linea = valor, linea

class NotaSt:
    def __init__(self, nota, duracion, linea):
        self.nota, self.duracion, self.linea = nota, duracion, linea

class Acorde:
    def __init__(self, notas, linea):
        self.notas, self.linea = notas, linea     # notas: lista de str

class Silencio:
    def __init__(self, duracion, linea):
        self.duracion, self.linea = duracion, linea

class Repetir:
    def __init__(self, veces, sentencias, linea):
        self.veces, self.sentencias, self.linea = veces, sentencias, linea

# ===================== SCANNER (ply.lex) =====================
# Palabras clave en Mayuscula; las notas y duraciones van en minuscula (ID).
reservadas = {
    'Cancion': 'CANCION', 'Tempo': 'TEMPO', 'Nota': 'NOTA',
    'Acorde': 'ACORDE', 'Silencio': 'SILENCIO', 'Repetir': 'REPETIR',
}
tokens = ['ID', 'INT', 'STRING', 'LLAVEI', 'LLAVED', 'PUNTOYCOMA'] + list(reservadas.values())

t_LLAVEI = r'\{'
t_LLAVED = r'\}'
t_PUNTOYCOMA = r';'
t_ignore = ' \t\r'

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_PALABRA(t):
    r'[a-zA-Z]+'
    t.type = reservadas.get(t.value, 'ID')
    return t

def t_salto_linea(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise ErrorLexico(
        f"Error lexico en linea {t.lexer.lineno}: "
        f"caracter no reconocido '{t.value[0]}'.")

lexer = lex.lex()

# ===================== PARSER (ply.yacc) =====================
def p_cancion(p):
    '''cancion : CANCION STRING LLAVEI sentencias LLAVED'''
    p[0] = Cancion(p[2], p[4])

def p_sentencias_lista(p):
    '''sentencias : sentencias sentencia'''
    p[0] = p[1] + [p[2]]

def p_sentencias_una(p):
    '''sentencias : sentencia'''
    p[0] = [p[1]]

def p_sentencia_tempo(p):
    '''sentencia : TEMPO INT PUNTOYCOMA'''
    p[0] = Tempo(p[2], p.lineno(1))

def p_sentencia_nota(p):
    '''sentencia : NOTA ID ID PUNTOYCOMA'''
    p[0] = NotaSt(p[2], p[3], p.lineno(1))

def p_sentencia_acorde(p):
    '''sentencia : ACORDE notas PUNTOYCOMA'''
    p[0] = Acorde(p[2], p.lineno(1))

def p_sentencia_silencio(p):
    '''sentencia : SILENCIO ID PUNTOYCOMA'''
    p[0] = Silencio(p[2], p.lineno(1))

def p_sentencia_repetir(p):
    '''sentencia : REPETIR INT LLAVEI sentencias LLAVED PUNTOYCOMA'''
    p[0] = Repetir(p[2], p[4], p.lineno(1))

def p_notas_lista(p):
    '''notas : notas ID'''
    p[0] = p[1] + [p[2]]

def p_notas_una(p):
    '''notas : ID'''
    p[0] = [p[1]]

def p_error(p):
    if p is None:
        raise ErrorSintactico(
            "Error sintactico: fin de entrada inesperado "
            "(falta un '}' o un ';'?).")
    raise ErrorSintactico(
        f"Error sintactico en linea {p.lineno}: "
        f"token inesperado '{p.value}'.")


parser = yacc.yacc(write_tables=False, debug=False, errorlog=yacc.NullLogger())


# ===================== ACCIONES SEMANTICAS =====================
NOTAS_VALIDAS = {'do', 're', 'mi', 'fa', 'sol', 'la', 'si'}
DURACIONES = {'redonda': 4.0, 'blanca': 2.0, 'negra': 1.0,
              'corchea': 0.5, 'semicorchea': 0.25}
TEMPO_DEFAULT = 100


class Interprete:
    def __init__(self):
        self.cant_tempos = 0
        self.tempo = None

    def analizar(self, cancion):
        beats = self._procesar(cancion.sentencias)
        if self.cant_tempos == 0:
            self.tempo = TEMPO_DEFAULT
        segundos = beats * 60.0 / self.tempo
        return {'nombre': cancion.nombre, 'beats': beats,
                'tempo': self.tempo, 'segundos': segundos}

    def _procesar(self, sentencias):
        return sum(self._ejecutar(s) for s in sentencias)

    def _ejecutar(self, s):
        if isinstance(s, Tempo):
            if s.valor <= 0:
                raise ErrorSemantico(
                    f"Error semantico en linea {s.linea}: el tempo debe ser "
                    f"mayor a 0 (se recibio {s.valor}).")
            self.cant_tempos += 1
            if self.cant_tempos > 1:
                raise ErrorSemantico(
                    f"Error semantico en linea {s.linea}: el Tempo solo puede "
                    f"definirse una vez.")
            self.tempo = s.valor
            return 0.0

        if isinstance(s, NotaSt):
            self._validar_nota(s.nota, s.linea)
            return self._validar_duracion(s.duracion, s.linea)

        if isinstance(s, Silencio):
            return self._validar_duracion(s.duracion, s.linea)

        if isinstance(s, Acorde):
            if len(s.notas) < 2:
                raise ErrorSemantico(
                    f"Error semantico en linea {s.linea}: un acorde debe tener "
                    f"al menos 2 notas.")
            for n in s.notas:
                self._validar_nota(n, s.linea)
            return 1.0   # un acorde dura una negra

        if isinstance(s, Repetir):
            if s.veces < 1:
                raise ErrorSemantico(
                    f"Error semantico en linea {s.linea}: Repetir debe ser al "
                    f"menos 1 vez (se recibio {s.veces}).")
            return s.veces * self._procesar(s.sentencias)

        raise ErrorSemantico(f"Sentencia desconocida: {s!r}")

    def _validar_nota(self, nombre, linea):
        if nombre not in NOTAS_VALIDAS:
            raise ErrorSemantico(
                f"Error semantico en linea {linea}: '{nombre}' no es una nota "
                f"valida (do re mi fa sol la si).")

    def _validar_duracion(self, nombre, linea):
        if nombre not in DURACIONES:
            raise ErrorSemantico(
                f"Error semantico en linea {linea}: '{nombre}' no es una "
                f"duracion valida (redonda blanca negra corchea semicorchea).")
        return DURACIONES[nombre]


def analizar(codigo):
    """Compila y analiza la cancion. Devuelve un dict con el resumen.
    Lanza ErrorLexico / ErrorSintactico / ErrorSemantico."""
    lexer.lineno = 1
    arbol = parser.parse(codigo, lexer=lexer)
    return Interprete().analizar(arbol)


def reproducir(codigo):
    r = analizar(codigo)
    print(f"Cancion \"{r['nombre']}\": {r['beats']:g} negras, "
          f"{r['segundos']:.2f} s a {r['tempo']} bpm")
    return r


EJEMPLO = '''Cancion "Escala alegre" {
    Tempo 120;
    Nota do negra;
    Nota re negra;
    Nota mi blanca;
    Acorde do mi sol;
    Silencio negra;
    Repetir 2 {
        Nota sol corchea;
        Nota la corchea;
    };
}'''
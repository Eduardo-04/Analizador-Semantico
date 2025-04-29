import re

# Definir los patrones para los tokens
TOKEN_PATTERNS = [
    ("Correo Electrónico", r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
    ("Palabra Reservada", r"\b(if|else|while|for|return|int|float|char|string|void|INSERT|SELECT|UPDATE|DELETE|FROM|WHERE|INTO|VALUES)\b"),
    ("Número Decimal", r"\b\d+\.\d*\b|\b\.\d+\b"),
    ("Número Entero", r"\b\d+\b(?!\.)"),
    ("Operador", r"[+\-*/=<>!]"),
    ("Símbolo", r"[(){};,]"),
    ("Identificador", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
    ("Cadena", r'"[^"]*"|\'[^\']*\''),
    ("Comentario", r"//.*|/\*.*?\*/"),
]

class TablaSimbolos:
    def __init__(self):
        self.simbolos = []
        self.errores = []
    
    def agregar(self, identificador, tipo, valor=None):
        # Verificar si el identificador ya existe
        for sim in self.simbolos:
            if sim['Identificador'] == identificador:
                self.errores.append(f"Error semántico: El identificador '{identificador}' ya fue declarado")
                return False
        
        # Verificar restricciones de nombres
        if identificador[0].isdigit():
            self.errores.append(f"Error semántico: El identificador '{identificador}' no puede comenzar con número")
            return False
        
        # Verificar mayúsculas según tipo de palabra
        if tipo in ['INSERT', 'SELECT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'INTO', 'VALUES']:
            if not identificador.isupper():
                self.errores.append(f"Error semántico: Palabra reservada SQL '{identificador}' debe estar en mayúsculas")
                return False
        elif tipo in ['int', 'float', 'char', 'string', 'void', 'if', 'else', 'while', 'for', 'return']:
            if not identificador.islower():
                self.errores.append(f"Error semántico: Palabra reservada de programación '{identificador}' debe estar en minúsculas")
                return False
        
        # Agregar a la tabla
        self.simbolos.append({
            'Identificador': identificador,
            'Tipo': tipo,
            'Valor': valor
        })
        return True
    
    def actualizar(self, identificador, valor):
        encontrado = False
        for sim in self.simbolos:
            if sim['Identificador'] == identificador:
                # Verificar tipo al actualizar
                if sim['Tipo'] == 'int' and not str(valor).isdigit():
                    self.errores.append(f"Error semántico: No se puede asignar valor no entero a variable '{identificador}' de tipo int")
                    return False
                elif sim['Tipo'] == 'float' and not re.match(r"^\d+\.\d*$|^\.\d+$", str(valor)):
                    self.errores.append(f"Error semántico: No se puede asignar valor no decimal a variable '{identificador}' de tipo float")
                    return False
                elif sim['Tipo'] == 'char' and (not isinstance(valor, str) or len(valor) != 3 or valor[0] != "'" or valor[2] != "'"):
                    self.errores.append(f"Error semántico: No se puede asignar valor no carácter a variable '{identificador}' de tipo char")
                    return False
                
                sim['Valor'] = valor
                encontrado = True
                break
        
        if not encontrado:
            self.errores.append(f"Error semántico: El identificador '{identificador}' no ha sido declarado")
            return False
        return True
    
    def buscar(self, identificador):
        for sim in self.simbolos:
            if sim['Identificador'] == identificador:
                return sim
        return None
    
    def mostrar(self):
        print("\nTabla de Símbolos:")
        print("| Identificador | Tipo   | Valor               |")
        print("|---------------|--------|---------------------|")
        for sim in self.simbolos:
            valor = str(sim['Valor'])[:20]  # Limitar longitud de valor para visualización
            print(f"| {sim['Identificador'].ljust(14)} | {sim['Tipo'].ljust(7)} | {valor.ljust(20)} |")

def analizar_codigo(codigo):
    tokens = []
    index = 0

    while index < len(codigo):
        match = None
        for tipo, patron in TOKEN_PATTERNS:
            regex = re.compile(patron)
            match = regex.match(codigo, index)
            if match:
                valor = match.group()
                # Saltar comentarios
                if tipo == "Comentario":
                    index += len(valor)
                    break
                tokens.append((valor, tipo))
                index += len(valor)
                break
        
        if not match:
            if codigo[index].isspace():
                index += 1
            else:
                tokens.append((codigo[index], "Inválido"))
                index += 1

    return tokens

def verificar_sintaxis(tokens):
    errores = []
    for i, (token, tipo) in enumerate(tokens):
        if tipo == "Correo Electrónico":
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", token):
                errores.append(f"Error de sintaxis: '{token}' no es un correo electrónico válido.")
        elif tipo == "Inválido":
            if "@" in token or "." in token:
                errores.append(f"Error de sintaxis: '{token}' no es un correo electrónico válido. Falta el símbolo '@' o el dominio.")
    
    return errores

def analisis_semantico(tokens, tabla_simbolos):
    i = 0
    n = len(tokens)
    while i < n:
        token, tipo = tokens[i]
        
        # Verificar declaración de variables
        if tipo == "Palabra Reservada" and token in ['int', 'float', 'char', 'string']:
            tipo_var = token
            i += 1
            if i < n and tokens[i][1] == "Identificador":
                nombre_var = tokens[i][0]
                i += 1
                if i < n and tokens[i][0] == '=':
                    i += 1
                    if i < n:
                        valor_token, valor_tipo = tokens[i]
                        valor = valor_token
                        
                        # Verificar tipos
                        if tipo_var == 'int' and valor_tipo != "Número Entero":
                            tabla_simbolos.errores.append(f"Error semántico: No se puede asignar {valor} a variable {nombre_var} de tipo {tipo_var}")
                        elif tipo_var == 'float' and valor_tipo != "Número Decimal":
                            tabla_simbolos.errores.append(f"Error semántico: No se puede asignar {valor} a variable {nombre_var} de tipo {tipo_var}")
                        elif tipo_var == 'char' and valor_tipo != "Cadena":
                            tabla_simbolos.errores.append(f"Error semántico: No se puede asignar {valor} a variable {nombre_var} de tipo {tipo_var}")
                        elif tipo_var == 'string' and valor_tipo not in ["Cadena", "Correo Electrónico"]:
                            tabla_simbolos.errores.append(f"Error semántico: No se puede asignar {valor} a variable {nombre_var} de tipo {tipo_var}")
                        
                        # Verificar correo electrónico para strings
                        if tipo_var == 'string' and valor_tipo == "Cadena" and '@' in valor:
                            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", valor.strip('"\'')):
                                tabla_simbolos.errores.append(f"Error semántico: '{valor}' no es un correo electrónico válido")
                        
                        tabla_simbolos.agregar(nombre_var, tipo_var, valor)
                        i += 1
                else:
                    tabla_simbolos.agregar(nombre_var, tipo_var)
        
        # Verificar operaciones entre tipos incompatibles
        elif tipo == "Identificador":
            var1 = tabla_simbolos.buscar(token)
            if var1:
                if i+2 < n and tokens[i+1][0] in ['+', '-', '*', '/']:
                    op = tokens[i+1][0]
                    token2, tipo2 = tokens[i+2]
                    if tipo2 == "Identificador":
                        var2 = tabla_simbolos.buscar(token2)
                        if var2:
                            if var1['Tipo'] != var2['Tipo']:
                                tabla_simbolos.errores.append(f"Error semántico: No se puede operar {var1['Tipo']} '{var1['Identificador']}' con {var2['Tipo']} '{var2['Identificador']}'")
                    elif tipo2 in ["Número Entero", "Número Decimal"]:
                        if var1['Tipo'] not in ['int', 'float']:
                            tabla_simbolos.errores.append(f"Error semántico: No se puede operar {var1['Tipo']} '{var1['Identificador']}' con número")
        
        # Verificar sentencias SQL terminan con ;
        elif tipo == "Palabra Reservada" and token in ['INSERT', 'SELECT', 'UPDATE', 'DELETE']:
            encontro_punto_coma = False
            j = i
            while j < n and tokens[j][0] != ';':
                j += 1
            if j >= n or tokens[j][0] != ';':
                tabla_simbolos.errores.append(f"Error semántico: Sentencia SQL '{token}...' debe terminar con ';'")
            else:
                i = j
        
        i += 1

def mostrar_tokens(tokens):
    print("\nTokens encontrados:")
    print("Token".ljust(20), "Tipo")
    print("-" * 40)
    for token, tipo in tokens:
        print(f"{token.ljust(20)} {tipo}")

def main():
    print("ANALIZADOR SEMÁNTICO INTERACTIVO")
    print("Ingrese el código a analizar (escriba 'fin' en una línea nueva para terminar):")
    
    # Leer múltiples líneas de entrada hasta que el usuario escriba 'fin'
    lineas = []
    while True:
        linea = input()
        if linea.lower() == 'fin':
            break
        lineas.append(linea)
    
    codigo = '\n'.join(lineas)
    
    # Crear tabla de símbolos
    tabla_simbolos = TablaSimbolos()
    
    # Análisis léxico
    tokens = analizar_codigo(codigo)
    mostrar_tokens(tokens)
    
    # Análisis sintáctico
    errores_sintaxis = verificar_sintaxis(tokens)
    for error in errores_sintaxis:
        tabla_simbolos.errores.append(error)
    
    # Análisis semántico
    analisis_semantico(tokens, tabla_simbolos)
    
    # Mostrar resultados
    tabla_simbolos.mostrar()
    
    # Mostrar errores
    if tabla_simbolos.errores:
        print("\nErrores encontrados:")
        for error in tabla_simbolos.errores:
            print(f"- {error}")
    else:
        print("\nNo se encontraron errores semánticos.")

if __name__ == "__main__":
    main()
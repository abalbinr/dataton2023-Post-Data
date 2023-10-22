def definirVariablesDecision(trabajadores, franjas):
    x = pulp.LpVariable.dicts('Duplas binarias', [(i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)
    return x


# Variable intermedia para almacenar las diferencias
# Función objetivo absoluto (Con condicionales)

def definirDiccionariosDiferencia(franjas):
    diferencias = pulp.LpVariable.dicts('diferencia', franjas)
    return diferencias



def agregarRestriccionesDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x):
    global problem
    global franjasTotales

    
    for t in franjas:
        if (len(franjas) != franjasTotales):
            t = t-16
        problem += diferencias[t] == demanda_clientes[t] - pulp.lpSum(x[(i, t)] for i in trabajadores)



def agregarFuncionObjetivoModelo(diferencias,franjas):
    global problem
    problem += pulp.lpSum(diferencias[t] if (diferencias[t]>=0) else -diferencias[t] for t in franjas ), "Sumatoria de diferencias absolutas"



# No se usan variables intermedias
# Función objetivo absoluto (Con condicionales)
"""
def agregarFuncionObjetivoModelo(franjas, demanda_clientes, x):
    global problem
    problem += pulp.lpSum((demanda_clientes[t] - pulp.lpSum(x[(i, t)])) if ((demanda_clientes[t] - pulp.lpSum(x[(i, t)])) >= 0) else (-1*(demanda_clientes[t] - pulp.lpSum(x[(i, t)]))) for t in franjas for i in trabajadores), "Sumatoria de las diferencias absolutas entre la demanda y la cantidad de trabajadores"

    """

def agregarRestriccionfranjasTrabajadasModelo(trabajadores, franjas, x, numMinimo, numMaximo):
    global problem
    for i in trabajadores:
        problem += pulp.lpSum(x[(i, t)] for t in franjas) >= numMinimo
        problem += pulp.lpSum(x[(i, t)] for t in franjas) <= numMaximo


def agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, x):
    global problem
    for t in franjas:
        problem += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1


# (Temporal) Ya no se está usando esta función pero es para tenerla como referencia
def agregarRestriccionAlmuerzoModelo(trabajadores, franjas, x):
    ## El almurzo debe ser entre 11:30 (Flanja 16) y maximo hasta las 15:00 (Flanja 30 no inclusive)
    ## entonces entre esas 14 franjas debe descansar 6 franjas para el almuerzo, 
    ## además entre ese tiempo solo es posible sacar maximo 1 pausa activa
    ## En conlusión, en esa bloque de 14 franjas se debe trabajar entre 7 y 8 franjas

    global problem
    for i in trabajadores:
        problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) >= 7
        problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) <= 8


def agregarRestriccionAlmuerzoContinuoModelo(trabajadores, franjas, x, iniciosAlmuerzo):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia a almorzar ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosAlmuerzo[indexTrabajador]
        if (flanjaInicial != -1):
            # El trabajador no puede trabajar durante las 6 franjas del almuerzo
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial:flanjaInicial+6]) == 0

def agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(trabajadores, franjas, x, iniciosAlmuerzos):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia a almorzar ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosAlmuerzos[indexTrabajador]
        if (flanjaInicial != -1):
            # Cada trabajador tiene que trabajar 1 hora continua antes y despues de almorzar
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial-4:flanjaInicial]) == 4
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial+6:flanjaInicial+10]) == 4


def agregarRestriccionNoTrabajaAntesInicioJornadaModelo(trabajadores, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia la jornada ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosJornadas[indexTrabajador]
        if (flanjaInicial != -1):
            # El trabajador no puede trabajar antes de iniciar de jornada
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[0:flanjaInicial]) == 0


def agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(trabajadores, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia la jornada ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosJornadas[indexTrabajador]
        if (flanjaInicial != -1):
            # El trabajador no puede trabajar despues de finalizar su jornada
            # El trabajador finaliza su jornada 38 flanjas despues de iniciar la jornada
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial+38:len(franjas)]) == 0


def agregarRestriccionTrabajaContinuoExtremosJornadaModelo(trabajadores, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia la jornada ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosJornadas[indexTrabajador]
        if (flanjaInicial != -1):
            # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio y antes de su jornada final (Es decir, trabajar 1 hora continua en los extremos)
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial:flanjaInicial+4]) == 4
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial+34:flanjaInicial+38]) == 4


def agregarRestriccionPausasActivasModelo(trabajadores, franjas, x, iniciosAlmuerzos, iniciosJornadas):
    # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    # Eso se traduce a que en cada intervalo de 5 flanjas la suma debe dar mayor o igual a 4 (Maximo una pausa activa)
    # Y además, traduce que en cada intervalo de 9 flanjas no puede sumar 9 flanjas trabajadas 
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque si se sabe cuando inicia la jornada ese trabajador y cuando inicia el almuerzo
        # En caso contrario, no se sabe
        flanjaInicialJornada = iniciosJornadas[indexTrabajador]
        flanjaInicialAlmuerzo = iniciosAlmuerzos[indexTrabajador]

        if (flanjaInicialJornada != -1 and flanjaInicialAlmuerzo != -1):
            
            ## Antes de almorzar
            for flanjaEspecifica in range(flanjaInicialJornada,flanjaInicialAlmuerzo-4):
                
                # Intervalos de 5 deben sumar 4 o 5 flanjas trabajadas
                problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaEspecifica:flanjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 flanjas trabajadas
                problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaEspecifica:flanjaEspecifica+9]) <= 8
            
            ## Despues de almorzar
            for flanjaEspecifica in range(flanjaInicialAlmuerzo+6,flanjaInicialJornada+34):

                # Intervalos de 5 deben sumar 4 o 5 flanjas trabajadas
                problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaEspecifica:flanjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 flanjas trabajadas
                if (flanjaEspecifica < len(franjas)-9):
                    problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaEspecifica:flanjaEspecifica+9]) <= 8


def crearExcelConResultadosOptimos(trabajadores, franjas, x, iniciosAlmuerzos):
    global fecha_hora

    horas = [str(i).split()[1] for i in fecha_hora]

    documentoOptimo = []
    estadoOptimo = []
    horaOptimo = []
    franjaOptimo = []

    for t in franjas:
        for i in trabajadores:
            documentoOptimo += [i]
            
            if pulp.value(x[(i, t)]) == 1:
                estadoOptimo += ["Trabaja"]
            else:
                estadoOptimo += ["Nada"]
            
            horaOptimo += [horas[t]]
            franjaOptimo += [t+30]
                
    suc_codeOptimo = [60]*(len(franjas)*len(trabajadores))
    fechaOptimo = [str(fecha_hora[0]).split()[0]]*(len(franjas)*len(trabajadores))


    data = {'suc_code': suc_codeOptimo, 'documento': documentoOptimo, 'fecha': fechaOptimo, 'hora': horaOptimo, 'estado': estadoOptimo, 'hora_franja': franjaOptimo}
    solucionOptima = pd.DataFrame(data)
    solucionOptima = solucionOptima.sort_values(by=['documento','hora_franja'])

    solucionOptima.to_excel("./src/PuLP/solucionOptima.xlsx", index=False)

    ## Proximamente se borrará el código anterior
    ## Archivo CSV
    horas = [str(i).split()[1] for i in fecha_hora]

    documentoOptimo = []
    estadoOptimo = []
    horaOptimo = []
    franjaOptimo = []

    for t in franjas:
        for i in trabajadores:
            documentoOptimo += [i]
            
            if pulp.value(x[(i, t)]) == 1:
                estadoOptimo += ["Trabaja"]
            else:
                if (t != 0 and t != 45):
                    if(t in range(iniciosAlmuerzos[i-1],iniciosAlmuerzos[i-1]+6)):
                        estadoOptimo += ["Almuerza"]
                    elif (pulp.value(x[(i, t-1)]) == 1 and pulp.value(x[(i, t+1)]) == 1):
                        estadoOptimo += ["Pausa Activa"]
                    else:
                        estadoOptimo += ["Nada"]
                else:
                    estadoOptimo += ["Nada"]
            
            horaOptimo += [horas[t]]
            franjaOptimo += [t+30]
                
    suc_codeOptimo = [60]*(len(franjas)*len(trabajadores))
    fechaOptimo = [str(fecha_hora[0]).split()[0]]*(len(franjas)*len(trabajadores))


    data = {'suc_cod': suc_codeOptimo, 'documento': documentoOptimo, 'fecha': fechaOptimo, 'hora': horaOptimo, 'estado': estadoOptimo, 'hora_franja': franjaOptimo}
    solucionOptima = pd.DataFrame(data)
    solucionOptima = solucionOptima.sort_values(by=['documento','hora_franja'])

    solucionOptima.to_csv("./src/PuLP/solucionOptima.csv", index=False) 

    print("Asignación Óptima de Horarios realizada")


def optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas):
    global problem
    global franjasTotales
    global final

    # Crea un problema (Modelo) de minimización lineal
    problem = pulp.LpProblem("OptimizacionJornadas", pulp.LpMinimize)

    # Define las variables de decisión
    x = definirVariablesDecision(trabajadores, franjas)

    ### Con variable intermedia (Diferencias)
    
    # Define un diccionario para almacenar las diferencias de cada franja
    diferencias = definirDiccionariosDiferencia(franjas)

    # Agrega las restricciones de las diferencias
    agregarRestriccionesDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x)
    
    # Agrega la función objetivo para minimizar las diferencias
    agregarFuncionObjetivoModelo(diferencias,franjas)

    

    ### Sin variables intermedias
    """
    # Agrega la función objetivo para minimizar las diferencias 
    agregarFuncionObjetivoModelo(franjas, demanda_clientes, x)
    """

    # Agrega las restricciones de las variables de decisión

    #El código de optimización se puede reutilizar para tramos de franjas, entonces solo aplicar esta restricción cuando se tenga todas las franjas
    if (len(franjas) == franjasTotales):
        ## Cada trabajador tiene que trabajar 8 horas al dia
        ## (Sin son franjas de 15 min entonces 8 horas son 32 franjas al dia)
        ## Pero hay que tener en cuenta que hay pausas activas. En general un trabajador puede sacar entre 2-6 pausas activas dependiendo de como las saca.
        ## Entonces solo tiene que trabajar minimo 26 franjas y maximo 30 franjas 
        agregarRestriccionfranjasTrabajadasModelo(trabajadores, franjas, x, 26, 30)

    ## Cada flanja debe ser atendida por al menos un trabajador
    agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, x)

    ## Cada trabajador debe sacar 1h 30 min continua de almuerzo (6 franjas)
    ## El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)
    ## Cada trabajador debe iniciar a almorzar entre la flanja 16 y 24 (Inclusives)
    agregarRestriccionAlmuerzoContinuoModelo(trabajadores, franjas, x, iniciosAlmuerzos)

    ## Cada trabajador tiene que trabajar 1 hora continua antes y despues del almuerzo
    agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(trabajadores, franjas, x, iniciosAlmuerzos)

    ## Cada trabajador no puede trabajar antes de su jornada inicio
    agregarRestriccionNoTrabajaAntesInicioJornadaModelo(trabajadores, franjas, x, iniciosJornadas)

    ## Cada trabajador no puede trabajar despues de su jornada final
    agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(trabajadores, franjas, x, iniciosJornadas)

    ## Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio y antes de su jornada final (Es decir, trabajar 1 hora continua en los extremos)
    agregarRestriccionTrabajaContinuoExtremosJornadaModelo(trabajadores, franjas, x, iniciosJornadas)

    ## Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    agregarRestriccionPausasActivasModelo(trabajadores, franjas, x, iniciosAlmuerzos, iniciosJornadas)

    # Resuelve el problema
    problem.solve()

    # Imprime el estado del problema (óptimo, subóptimo, etc.)
    print("Estado:", pulp.LpStatus[problem.status])

    # Imprime el valor optimo de la diferencia
    print("Valor optimo de la Diferencia:", pulp.value(problem.objective))

    # Guarda la asignación óptima de horarios en un excel
    ## Solo si es el modelo final
    if (final):
        crearExcelConResultadosOptimos(trabajadores, franjas, x, iniciosAlmuerzos)


def encontrarIniciosOptimos(trabajadores, franjas, demanda_clientes, numMin, numMax, iniciosAlmuerzos, iniciosJornadas, buscar):
    # El objetivo es encontrar los inicios de almuerzos y jornadas:
    # Si no se ingresa inicios de almuerzo e inicios Jornadas, es porque por defecto es [-1,-1,-1,-1,-1,-1,-1,-1] para representar que aun no se han encontrado.

    global problem

    # Encuentra la flanja inicial de cada trabajador
    for indexTrabajador in range(len(trabajadores)):
        valoresOptimos = []
        franjasOptimas = []

        # cada trabajador debe iniciar a almorzar entre la flanja 16 y 24 (Inclusives)
        # cada trabajador debe iniciar su jornada entre la flanja 0 y 8 (Inclusives)
        for flanjaInicial in range(numMin,numMax+1):
            if (buscar == "buscarAlmuerzos"):
                iniciosAlmuerzos[indexTrabajador] = flanjaInicial
            else:
                iniciosJornadas[indexTrabajador] = flanjaInicial

            optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas)

            if (pulp.LpStatus[problem.status] == "Optimal"):
                valoresOptimos += [pulp.value(problem.objective)]
                franjasOptimas += [flanjaInicial]
        if (len(valoresOptimos) > 0):
            maxValorOptimo = max(valoresOptimos)
            indiceMaxOptimo = valoresOptimos.index(maxValorOptimo) #Primera Ocurrencia
            flanjaOptimaTrabajador = franjasOptimas[indiceMaxOptimo]

        if (buscar == 'buscarAlmuerzos'):
            iniciosAlmuerzos[indexTrabajador] = flanjaOptimaTrabajador
        else:
            iniciosJornadas[indexTrabajador] = flanjaOptimaTrabajador

    if (buscar == 'buscarAlmuerzos'):
        return iniciosAlmuerzos
    else:
        return iniciosJornadas



#Inicio del Main

import pulp
import pandas as pd

# Extración de datos del excel
dataton2023 = './src/PuLP/Dataton2023_Etapa1.xlsx'

demanda_df = pd.read_excel(dataton2023, sheet_name='demand')
trabajadores_df = pd.read_excel(dataton2023, sheet_name='workers')

# Variables completas
fecha_hora = list(demanda_df.fecha_hora)
demanda_clientes = list(demanda_df.demanda)
trabajadores = list(trabajadores_df.documento)
franjas = list(range(0, len(demanda_clientes)))  # De 0 (7:30am) hasta la ultima demanda registrada (de 0-45)
franjasTotales = len(franjas)

# Encontrar inicios optimos de almuerzo y jornadas
final = False
iniciosAlmuerzos = [16,17,18,19,20,21,22,24]
iniciosJornadas = [0,1,2,3,4,5,6,8]
for i in range(2):
    # Encuentra las franjas iniciales del almuerzo de cada trabajador
    problem = pulp.LpProblem("OptimizacionIniciosAlmuerzo", pulp.LpMinimize)
    ## cada trabajador debe iniciar a almorzar entre la flanja 16 y 24 (Inclusives)
    iniciosAlmuerzos = encontrarIniciosOptimos(trabajadores, franjas, demanda_clientes, 16, 24, iniciosAlmuerzos, iniciosJornadas, "buscarAlmuerzos")

    # Encuentra las franjas iniciales de la jornada de cada trabajador
    problem = pulp.LpProblem("OptimizacionInicioJornadas", pulp.LpMinimize)
    # cada trabajador debe iniciar su jornada entre la flanja 0 y 8 (Inclusives)
    iniciosJornadas = encontrarIniciosOptimos(trabajadores, franjas, demanda_clientes, 0, 8, iniciosAlmuerzos,iniciosJornadas, "buscarJornadas")

## Modelo final
final = True
problem = pulp.LpProblem("OptimizacionJornadasFinal", pulp.LpMinimize)
optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas)

print(iniciosAlmuerzos)
print(iniciosJornadas)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import Solucion
df_solucion = pd.read_excel('.\src\PuLP\solucionOptima.xlsx')
Solucion.mostrarSolucion(df_solucion)
import datetime
from email.policy import default
import re
from xml.dom import ValidationErr
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class Carrera(models.Model):
    _name = "ma.carrera"
    _description = "Carrera"
    name = fields.Char(string="Nombre de la Carrera", required=True)
    numero_ciclos = fields.Integer(string="Número de Ciclos", required=True)
    duracion_horas = fields.Integer(string="Duración en Horas", required=True)

class GrupoSocioeconomico(models.Model):
    _name = "ma.grupo_socioeconomico"
    _description = "Grupo Socioeconómico"
    name = fields.Char(string="Grupo Socioeconómico", required=True)
    arancel = fields.Float(string='Arancel', digits=(8, 2), required=True)
    matricula = fields.Float(string='Matrícula', digits=(8, 2), required=True)

class CostoOptimo(models.Model):
    _name = "ma.costo_optimo"
    _description = "Costo Óptimo"
    name = fields.Char(string="Régimen", required=True)
    valor = fields.Float(string='Valor', digits=(8, 2), required=True)

class Matricula(models.Model):
    _name = "ma.matricula"
    _description = "Matricula"
    decano = fields.Char(string="Nombre del Decano", default="Ing. Julio Eduardo Romero Sigcho Mgs.")
    name = fields.Char(string="Nombre", required=True, default=lambda self: self.env['res.users'].search([('id', '=', self.env.uid)], limit=1).name)
    cedula_alumno = fields.Char(string="Cédula", required=True)

    user_id = fields.Many2one(
        "res.users", string="Alumno",
        default=lambda self: self.env.uid,
        ondelete="cascade")

    carrera_id = fields.Many2one(
        "ma.carrera", string="Carrera",
        default=lambda self: self.env['ma.carrera'].search([], limit=1),
        ondelete="cascade")

    periodo_id = fields.Many2one(
        "ma.periodomatricula", string="Periodo Matrícula",
        default=lambda self: self.env['ma.periodomatricula'].search([('estado', '=', True)], limit=1),
        ondelete="cascade")
  
    # tercera matricula datos
    ciclo_materias_reprobadas_tercera = fields.Many2one("ma.ciclo", string="Ciclo en el cual reprobó la materia en tercera matricula")
    paralelo_ciclo_reprobar_tercera = fields.Many2one("ma.paralelo", string="Paralelo del Ciclo en el cual reprobó asignaturas")
    asignaturas_reprobadas_tercera = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel3',
        'asignatura_id', 'ciclo_id', string='Asignaturas Reprobadas por Tercera matricula')

    #segunda matricula datos
    ciclo_materias_reprobadas = fields.Many2one("ma.ciclo", string="Ciclo en el cual reprobó asignaturas")
    
    # Campo para Paralelo y validaciones
    paralelo_ciclo_reprobar = fields.Many2one("ma.paralelo", string="Paralelo del Ciclo en el cual reprobó asignaturas")
    asignaturas_reprobadas = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel2',
        'asignatura_id', 'ciclo_id', string='Asignaturas Reprobadas por Segunda Matricula')

    #datos primera matricula
    ciclo_materias_pendientes = fields.Many2one("ma.ciclo", string="Ciclo en el cual tiene materias pendientes")
    asignaturas_pendientes = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel1',
        'asignatura_id', 'ciclo_id', string='Asignaturas Pendientes')

    #Campo para ciclo a matrícular
    #Campo para guardar la respuesta luego de aplicar las normas de la U
    ciclo_matricular_especial = fields.Many2one("ma.ciclo", string="Ciclo en el cual desea matricularse")
    validar_matricula_1_2 = fields.Boolean(string="Validar primera Matrícula", default=False)
    asignaturas_tercera = fields.Char(string="Materias matricular 3")
    asignaturas_segunda = fields.Char(string="Materias matricular 2")
    asignaturas_primera = fields.Char(string="Materias matricular 1")
    ciclo_matricular = fields.Char(string="Ciclo en el que se va a matricular")
    ciclo_matricular_especial2 = fields.Char(string="Ciclo especial")

    #choque de horario
    materias_horario_choque = fields.Char(string="Materias que chocan")

    #costo de matricula
    valores_pagar = fields.Char(string="Valores a pagar")
    calcular_valores = fields.Boolean(string="Calcular valores por pérdida de Gratuidad", default=False)
    grupo_socioeconomico_id = fields.Many2one(
        "ma.grupo_socioeconomico", string="Grupo Socioeconómico",
        default=lambda self: self.env['ma.grupo_socioeconomico'].search([], limit=1),
        ondelete="cascade")

    costo_optimo_id = fields.Many2one(
        "ma.costo_optimo", string="Costo Óptimo",
        default=lambda self: self.env['ma.costo_optimo'].search([], limit=1),
        ondelete="cascade")

    matricular_mismo_ciclo = fields.Boolean(string="Matricular solo en esta asignaturas", default=False)

    ocultar_resultados = fields.Boolean(string="Ocultar Resultados", default=False)

    solicitud_aprobado = fields.Boolean(string="Solicitud Aprobada", default=False)

    solicitud_rechazada = fields.Boolean(string="Solicitud Rechazada", default=False)

    asig_tercera_bool = fields.Boolean(string="¿Tiene asignatuas de tercera matrícula?", default=False)

    def eliminar_matriculas_diarias(self):
        matriculas = self.env["ma.matricula"].search([])
        for i in matriculas:
            i.unlink()

    def botonmatricular(self):
        self.ocultar_resultados = True
        carrera_id_ma = self.carrera_id.id
        asig_tercera_aux = []
        total_creditos_tercera = 0
        total_creditos_segunda = 0
        aux_materias_eliminar = ""
        aux_materias_eliminar2 = ""
        aux_materias_eliminar3 = ""
        bool_auxu = False
        contC2 = []
        for asig_tercera in self.asignaturas_reprobadas_tercera:
            total_creditos_tercera =  total_creditos_tercera + asig_tercera.creditos
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_tercera.ciclo_id.name))]
            aux1 = int(aux[0])
            if not(aux1 in contC2):
                contC2.append(aux1)
            if aux1 == 10:
                bool_auxu = True
            dato = [aux1, str(asig_tercera.ciclo_id.name), str(asig_tercera.name), str(asig_tercera.ciclo_id.id), asig_tercera.id]
            asig_tercera_aux.append(dato)

        asig_tercera_aux_ordenada = sorted(asig_tercera_aux, key=lambda x: x[0])
        if self.asignaturas_reprobadas_tercera:
            self.ciclo_matricular = asig_tercera_aux_ordenada[0][1]
            self.asignaturas_tercera = asig_tercera_aux_ordenada[0][2]
        asig_tercera_aux_ordenada = sorted(asig_tercera_aux, key=lambda x: x[0])
        asig_tercera_aux_ordenada_des = sorted(asig_tercera_aux, key=lambda x: x[0], reverse=True)

        #llenar primera matricula
        asig_primera_aux = []
        for asig_primera in self.asignaturas_pendientes:
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_primera.ciclo_id.name))]
            aux1 = int(aux[0])
            dato3 = [aux1, str(asig_primera.ciclo_id.name), str(asig_primera.name), str(asig_primera.ciclo_id.id), asig_primera.id]
            asig_primera_aux.append(dato3)

        #segunda matricula
        asig_segunda_aux = []
        ciclos_registados = []
        bool_aux = False
        contC = []
        for asig_segunda in self.asignaturas_reprobadas:
            total_creditos_segunda = total_creditos_segunda + asig_segunda.creditos
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_segunda.ciclo_id.name))]
            aux1 = int(aux[0])
            if not(aux1 in contC):
                contC.append(aux1)
            if aux1 == 10:
                bool_aux = True
            if aux1 not in ciclos_registados:
                ciclos_registados.append(aux1)
            dato2 = [aux1, str(asig_segunda.ciclo_id.name), str(asig_segunda.name), str(asig_segunda.ciclo_id.id), asig_segunda.id]
            asig_segunda_aux.append(dato2)

        asig_segunda_aux_ordenada = sorted(asig_segunda_aux, key=lambda x: x[0])
        asig_segunda_aux_ordenada_des = sorted(asig_segunda_aux, key=lambda x: x[0], reverse=True)
        ciclo_mayor=0
        id_ciclo = 0

        if self.asignaturas_reprobadas_tercera:
            self.ciclo_matricular = asig_tercera_aux_ordenada[0][1]
            ciclo_mayor = asig_tercera_aux_ordenada_des[0][0]
            id_ciclo = asig_tercera_aux_ordenada_des[0][3]

        if self.asignaturas_reprobadas:
            self.ciclo_matricular = asig_segunda_aux_ordenada[0][1]
            ciclo_mayor = asig_segunda_aux_ordenada_des[0][0]
            id_ciclo = asig_segunda_aux_ordenada_des[0][3]

        # ciclo anterior
        anterior_ciclo_matricular = ciclo_mayor - 1
        anterior_ciclo_matricular = "ciclo_" + str(anterior_ciclo_matricular)
        ciclo_anterior2 = self.env['ma.ciclo'].search(
            [('numero_ciclo', '=', anterior_ciclo_matricular), ('carrera_id', '=', carrera_id_ma)], limit=1)

        # ciclo siguiente
        nuevo_ciclo_matricular = ciclo_mayor - 2
        nuevo_ciclo_matricularA = "ciclo_" + str(nuevo_ciclo_matricular) 
        ciclo_siguiente2 = self.env['ma.ciclo'].search(
            [('numero_ciclo', '=', nuevo_ciclo_matricularA), ('carrera_id', '=', carrera_id_ma)], limit=1)

        ciclo = self.env['ma.ciclo'].search(
            [('id', '=', id_ciclo)])

        n_asignaturas = ciclo.n_asignaturas
        n_asignaturas = round(n_asignaturas * 0.40)
        c = 0
        s_aux_prerre = []
        s = ""
        materias_mismo_ciclo =""
        diferentes_ciclo = False

        for i in range(len(asig_segunda_aux_ordenada_des)):
            #if asig_segunda_aux_ordenada_des[i][0] != "":
            asignatura_validar = self.env['ma.asignatura'].search(
                [('id', '=', asig_segunda_aux_ordenada_des[i][4])])
            for j in range(len(asig_segunda_aux_ordenada_des)):
                for prerre in asignatura_validar.prerrequisitos:
                    if prerre.id == asig_segunda_aux_ordenada_des[j][4]:
                        s_aux_prerre.append(asig_segunda_aux_ordenada_des[i][2])

        aux_metodo = ""
        auxiliar = ""
        for i in range(len(asig_segunda_aux)):
            
            aux_metodo = aux_metodo + self.verificar_horario(ciclo.id, asig_segunda_aux[i][4]) + ","
            auxiliar = aux_metodo + self.verificar_horario(ciclo.id, asig_segunda_aux[i][4]) + ","
            
            if len(contC) > 1:
                
                if not(asig_segunda_aux[i][3] in auxiliar):
                    aux_metodo = aux_metodo + self.verificar_horario_bajo(ciclo_anterior2.id, asig_segunda_aux[i][4], ciclo_siguiente2.id) + ","
                   
                    aux_metodo = aux_metodo + self.verificar_horario_bajo(ciclo.id, asig_segunda_aux[i][4], ciclo_siguiente2.id) + ","
                         
        aux_metodo = aux_metodo.replace(",,", ",")
        aux_seperar = aux_metodo.split(',')

        for a in aux_seperar:
            if not (a == ',') or not(a ==''):
                s_aux_prerre.append(str(a))

        for i in range(len(asig_segunda_aux_ordenada_des)):
            if asig_segunda_aux_ordenada_des[i][0] != ciclo_mayor:
                diferentes_ciclo = True
            aux = asig_segunda_aux_ordenada_des[i][2]
            materias_mismo_ciclo = materias_mismo_ciclo + str(aux) + ", "

        for i in range(len(s_aux_prerre)):
            for j in range(len(asig_segunda_aux_ordenada_des)):
                print("Epa")
                print(asig_segunda_aux_ordenada_des[j][2])
                print(s_aux_prerre[i])
                if asig_segunda_aux_ordenada_des[j][2] == s_aux_prerre[i]:
                    asig_segunda_aux_ordenada_des[j] = ["", "", "", "", ""]

        #distinto ciclo
        for j in range(len(ciclos_registados)):
            for i in range(len(asig_segunda_aux_ordenada_des)):
                if asig_segunda_aux_ordenada_des[i][0] == ciclos_registados[j]:
                    c += 1
                    if c > n_asignaturas:
                        asig_segunda_aux_ordenada_des[i] = ["","","","",""]
            c = 0

        for i in range(len(asig_segunda_aux_ordenada_des)):
            if asig_segunda_aux_ordenada_des[i][0] != "":
                s = s + asig_segunda_aux_ordenada_des[i][2] + ", "
        
        if diferentes_ciclo:
            ciclos_agregar = []
            materias = s.split(sep=',')
            
            for m in materias:
                print(m)
                aux_asig = m.strip()
                materia = self.env['ma.asignatura'].search(
                    [('name', '=', aux_asig), ('carrera_id', '=' ,carrera_id_ma)], limit=1)
                if not(materia.ciclo_id.name in ciclos_agregar) and materia.ciclo_id.name != False:
                    print(materia.name)
                    print(materia.ciclo_id.name)
                    ciclos_agregar.append(materia.ciclo_id.name)
            especial = ""
            for i in range(len(ciclos_agregar)):
                especial = especial + str(ciclos_agregar[i]) + ","
            self.asignaturas_segunda = s
            self.ciclo_matricular_especial2 = especial

        else:
            self.asignaturas_segunda = materias_mismo_ciclo

        if self.asignaturas_reprobadas:
            self.ciclo_matricular = ciclo_mayor

        #primera matricula
        asig_primera_aux_ordenada = sorted(asig_primera_aux, key=lambda x: x[0])
        asig_primera_aux_ordenada_des = sorted(asig_primera_aux, key=lambda x: x[0], reverse=True)
        ciclo_mayor1 = 0
        id_ciclo = 0
        if self.asignaturas_pendientes:
            self.ciclo_matricular = asig_primera_aux_ordenada[0][1]
            ciclo_mayor1 = asig_primera_aux_ordenada_des[0][0]
            id_ciclo = asig_primera_aux_ordenada_des[0][3]

        ciclo = self.env['ma.ciclo'].search(
            [('id', '=', id_ciclo)])

        n_asignaturas1 = ciclo.n_asignaturas
        n_asignaturas1 = round(n_asignaturas1 * 0.40)
        print(n_asignaturas1)
        c = 0
        s = ""
        materias_mismo_ciclo1 = ""
        diferentes_ciclo = False

        for i in range(len(asig_primera_aux_ordenada_des)):
            if asig_primera_aux_ordenada_des[i][0] != ciclo_mayor1:
                diferentes_ciclo = True
            aux = asig_primera_aux_ordenada_des[i][2]
            materias_mismo_ciclo1 = materias_mismo_ciclo1 + str(aux) + ", "

        for i in range(len(asig_primera_aux_ordenada_des)):
            if asig_primera_aux_ordenada_des[i][0] == ciclo_mayor1:
                c += 1
                if c > n_asignaturas1:
                    asig_primera_aux_ordenada_des[i] = ["", "", ""]
            aux = asig_primera_aux_ordenada_des[i][2]
            s = s + str(aux) + ", "

        if diferentes_ciclo:
            self.asignaturas_primera = s
        else:
            self.asignaturas_primera = materias_mismo_ciclo1

        if self.asignaturas_pendientes:
            self.ciclo_matricular = ciclo_mayor1

        if len(asig_primera_aux) > 0 and len(asig_segunda_aux) >1:
            self.ciclo_matricular = ciclo_mayor

        nuevo_ciclo_matricular = "ciclo_" + str(self.ciclo_matricular)
        ciclo_final = self.env['ma.ciclo'].search(
            [('numero_ciclo', '=', nuevo_ciclo_matricular), ('carrera_id', '=', carrera_id_ma)], limit=1)
            
        self.ciclo_matricular = ciclo_final.name
        suma_creditos = 0
        creditos_asig = []
        creditos = 0

        #En segunda matrícula hay 2 o 1 asignatura y el resto de campos esta vacío.
        if (len(asig_segunda_aux) == 2 or len(asig_segunda_aux) == 1) and len(asig_primera_aux)==0 and len(asig_tercera_aux)==0:
            if self.matricular_mismo_ciclo == False:
                if ciclo_mayor >= 10:
                    nuevo_ciclo_matricular = 10
                else:
                    nuevo_ciclo_matricular = ciclo_mayor + 1

                nuevo_ciclo_matricular = "ciclo_" + str(nuevo_ciclo_matricular)
                ciclo_siguiente2 = self.env['ma.ciclo'].search(
                    [('numero_ciclo', '=', nuevo_ciclo_matricular), ('carrera_id', '=',carrera_id_ma)],limit=1)
                num_asig_aux = ciclo_siguiente2.n_asignaturas
                sesentaxciento_materias = round(int(num_asig_aux) * 0.6)

                if ciclo_siguiente2:
                    creditos_aux = ciclo_siguiente2.creditos
                    creditos = round(creditos_aux * 0.6)
                    asignaturas_ciclo_siguiente2 = self.env['ma.asignatura'].search(
                        [('ciclo_id', '=', ciclo_siguiente2.id)])

                name_asig = ""
                name_asig_correcto = ""
                for amayor in asignaturas_ciclo_siguiente2:
                    for i in range(len(asig_segunda_aux)):
                        print("eNTRA A HORARIO")
                        aux_materias_eliminar = self.verificar_horario(ciclo_siguiente2.id, asig_segunda_aux[i][4])
                        print(aux_materias_eliminar)
                        if aux_materias_eliminar != None:
                            name_asig = str(name_asig) + ", " + str(aux_materias_eliminar)
                        for prerre in amayor.prerrequisitos:
                            if str(prerre._origin.name) == str(asig_segunda_aux[i][2]):
                                aux_prerre = amayor.name + ", "
                                name_asig = name_asig + aux_prerre

                    if not(amayor.name in name_asig):
                        suma_creditos = suma_creditos + amayor.creditos
                        creditos_asig.append(amayor.creditos)
                        aux_prerre_si = amayor.name + ", "
                        name_asig_correcto = name_asig_correcto + aux_prerre_si

                materias_si = name_asig_correcto.split(sep=', ')
                for x in range(len(materias_si)):
                    if not materias_si[x]:
                        materias_si.pop(x)

                materias_add = ""

                for i in range(3):

                    if suma_creditos > creditos:
                        aux = len(materias_si)
                        aux_menor = 500
                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                print(materias_si[x])
                                aux = x
                                aux_menor = creditos_asig[x]

                        suma_creditos = suma_creditos - creditos_asig[aux]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                #aqui
                for i in range(3):
                    aux = 20
                    aux_menor = 500
                    if len(materias_si) > sesentaxciento_materias:

                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                aux = x
                                aux_menor = creditos_asig[x]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                for i in range(len(materias_si)):
                    materias_add= materias_add + materias_si[i]+","

                materias_add = materias_add.replace(',,','')
                self.asignaturas_primera = materias_add + ","
                self.asignaturas_primera = self.asignaturas_primera[:-1]
                self.asignaturas_primera = self.asignaturas_primera[:-1]

                self.asignaturas_tercera = ""
                
                self.ciclo_matricular = ciclo_siguiente2.name

                if bool_aux:
                    self.asignaturas_primera = ""

        #En segunda matrícula hay 1 y en asignaturas pendientes también hay 1.
        if len(asig_segunda_aux) == 1 and len(asig_primera_aux) == 1 and len(asig_tercera_aux)==0:
            if self.matricular_mismo_ciclo == False:

                #ciclo anterior
                anterior_ciclo_matricular = ciclo_mayor - 1
                anterior_ciclo_matricular = "ciclo_" + str(anterior_ciclo_matricular)
                print(anterior_ciclo_matricular)
                ciclo_anterior2 = self.env['ma.ciclo'].search(
                    [('numero_ciclo', '=', anterior_ciclo_matricular), ('carrera_id', '=', carrera_id_ma)], limit=1)

                #ciclo siguiente
                nuevo_ciclo_matricular = ciclo_mayor +1
                nuevo_ciclo_matricular = "ciclo_" + str(nuevo_ciclo_matricular)
                print(nuevo_ciclo_matricular)
                ciclo_siguiente2 = self.env['ma.ciclo'].search(
                    [('numero_ciclo', '=', nuevo_ciclo_matricular), ('carrera_id', '=',carrera_id_ma)], limit=1)

                # ciclo actual
                actual_ciclo_matricular = ciclo_mayor
                actual_ciclo_matricular = "ciclo_" + str(actual_ciclo_matricular)
                print(actual_ciclo_matricular)
                ciclo_actual2 = self.env['ma.ciclo'].search(
                    [('numero_ciclo', '=', actual_ciclo_matricular), ('carrera_id', '=', carrera_id_ma)], limit=1)

                if ciclo_siguiente2:
                    creditos_aux = ciclo_siguiente2.creditos
                    creditos = round(creditos_aux * 0.6)
                    asignaturas_ciclo_siguiente2 = self.env['ma.asignatura'].search(
                        [('ciclo_id', '=', ciclo_siguiente2.id)])

                num_asig_aux = ciclo_siguiente2.n_asignaturas
                sesentaxciento_materias = round(int(num_asig_aux) * 0.6)

                name_asig = ""
                name_asig_correcto = ""

                aux_materias_eliminar2 = self.verificar_horario_uni(ciclo_anterior2.id, asig_primera_aux[0][4],asig_segunda_aux[0][4])
                primera_puede = ""
                materia_choca = ""
                if aux_materias_eliminar2 != "":

                    aux_materias_eliminar2 = aux_materias_eliminar2.replace(",","")
                    materia_choca = self.asignaturas_segunda
                    materia_choca = materia_choca.replace(",", "")
                    if materia_choca:
                        materia_choca = materia_choca.replace(aux_materias_eliminar2, "")
                        
                    self.asignaturas_segunda = materia_choca

                    name_asig = name_asig + aux_materias_eliminar2
                    primera_puede = asig_primera_aux[0][2]
                aux_materias_eliminar3 = self.verificar_horario_bajo(ciclo_siguiente2.id, asig_primera_aux[0][4], asig_primera_aux[0][3])

                aux_materias_eliminar3 = aux_materias_eliminar3.replace(",", "")
                if aux_materias_eliminar3 != None:
                    name_asig = str(name_asig) + ", " + str(aux_materias_eliminar3)
                aux_materias_eliminar=""
                for amayor in asignaturas_ciclo_siguiente2:
                    for i in range(len(asig_segunda_aux)):
                        if not(materia_choca):
                            aux_materias_eliminar = self.verificar_horario(ciclo_siguiente2.id, asig_segunda_aux[i][4])
                        if aux_materias_eliminar != None:
                            name_asig = str(name_asig) + ", " + str(aux_materias_eliminar)
                        for prerre in amayor.prerrequisitos:
                            if str(prerre._origin.name) == str(asig_segunda_aux[i][2]):
                                aux_prerre = amayor.name + ", "
                                name_asig = name_asig + aux_prerre

                    if not(amayor.name in name_asig):
                        suma_creditos = suma_creditos + amayor.creditos
                        creditos_asig.append(amayor.creditos)
                        aux_prerre_si = amayor.name + ", "
                        name_asig_correcto = name_asig_correcto + aux_prerre_si

                materias_si = name_asig_correcto.split(sep=', ')
                for x in range(len(materias_si)):
                    if not materias_si[x]:
                        materias_si.pop(x)
                materias_add = ""

                for i in range(3):
                    if suma_creditos > creditos:
                        aux = len(materias_si)
                        aux_menor = 500
                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:

                                aux = x
                                aux_menor = creditos_asig[x]

                        suma_creditos = suma_creditos - creditos_asig[aux]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                for i in range(3):
                    aux = 20
                    aux_menor = 500
                    if len(materias_si) > sesentaxciento_materias:

                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                aux = x
                                aux_menor = creditos_asig[x]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                materias_add = materias_add + primera_puede + ","
                for i in range(len(materias_si)):
                    materias_add = materias_add + materias_si[i] + ","

                materias_add = materias_add.replace(',,', '')
                self.asignaturas_primera = materias_add + ","
                self.ciclo_matricular = ciclo_siguiente2.name

        suma_creditos = 0
        creditos_asig = []
        creditos = 0

        #En tercera matrícula hay 1 asignatura y el resto de campos esta vacío.
        if (len(asig_segunda_aux) == 0) and len(asig_primera_aux)==0 and len(asig_tercera_aux)==1:
            if self.matricular_mismo_ciclo == False:
                if ciclo_mayor >= 9:
                    nuevo_ciclo_matricular = 9
                else:
                    nuevo_ciclo_matricular = ciclo_mayor + 1

                nuevo_ciclo_matricular = "ciclo_" + str(nuevo_ciclo_matricular)
                ciclo_siguiente2 = self.env['ma.ciclo'].search(
                    [('numero_ciclo', '=', nuevo_ciclo_matricular), ('carrera_id', '=',carrera_id_ma)],limit=1)
                num_asig_aux = ciclo_siguiente2.n_asignaturas
                sesentaxciento_materias = round(int(num_asig_aux) * 0.6)

                if ciclo_siguiente2:
                    creditos_aux = ciclo_siguiente2.creditos
                    creditos = round(creditos_aux * 0.2)
                    asignaturas_ciclo_siguiente2 = self.env['ma.asignatura'].search(
                        [('ciclo_id', '=', ciclo_siguiente2.id)])

                name_asig = ""
                name_asig_correcto = ""
                for amayor in asignaturas_ciclo_siguiente2:
                    for i in range(len(asig_tercera_aux)):
                        print("eNTRA A HORARIO")
                        aux_materias_eliminar = self.verificar_horario(ciclo_siguiente2.id, asig_tercera_aux[i][4])
                        print(aux_materias_eliminar)
                        if aux_materias_eliminar != None:
                            name_asig = str(name_asig) + ", " + str(aux_materias_eliminar)
                        for prerre in amayor.prerrequisitos:
                            if str(prerre._origin.name) == str(asig_tercera_aux[i][2]):
                                aux_prerre = amayor.name + ", "
                                name_asig = name_asig + aux_prerre

                    if not(amayor.name in name_asig):
                        suma_creditos = suma_creditos + amayor.creditos
                        creditos_asig.append(amayor.creditos)
                        aux_prerre_si = amayor.name + ", "
                        name_asig_correcto = name_asig_correcto + aux_prerre_si

                materias_si = name_asig_correcto.split(sep=', ')
                
                for x in range(len(materias_si)):
                    if not materias_si[x]:
                        materias_si.pop(x)

                materias_add = ""

                for i in range(3):

                    if suma_creditos > creditos:
                        aux = len(materias_si)
                        aux_menor = 500
                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                print(materias_si[x])
                                aux = x
                                aux_menor = creditos_asig[x]

                        suma_creditos = suma_creditos - creditos_asig[aux]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                for i in range(3):
                    aux = 20
                    aux_menor = 500
                    if len(materias_si) > sesentaxciento_materias:
                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                aux = x
                                aux_menor = creditos_asig[x]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                for i in range(len(materias_si)):
                    materias_add= materias_add + materias_si[i]+","
            
                materias_add = materias_add.replace(',,','')
                materias_add = materias_add.replace(',,,','')
                self.asignaturas_primera = materias_add + ","
                self.ciclo_matricular = ciclo_siguiente2.name

                if bool_auxu:
                        self.asignaturas_primera = ""

                self.asignaturas_primera = self.asignaturas_primera.replace(",,", "")
                if self.asignaturas_primera == ",":
                    self.asignaturas_primera = self.asignaturas_primera[:-1]

        #En tercera matrícula hay 1 asignatura y el resto de campos esta vacío.
        if (len(asig_segunda_aux) >= 1) or len(asig_primera_aux)>=1 and len(asig_tercera_aux)==1:
            if self.matricular_mismo_ciclo == False:
                asig_mayor_cred_3 = 0
                asig_mayor_nombre_3 = ""
                asig_mayor_cred_2 = 0
                asig_mayor_nombre_2 = ""
                asig_mayor_cred_1 = 0
                asig_mayor_nombre_1 = ""

                if self.asignaturas_reprobadas_tercera:
                    for i in self.asignaturas_reprobadas_tercera:
                        if i.creditos > asig_mayor_cred_3:
                            asig_mayor_cred_3 = i.creditos
                            asig_mayor_nombre_3 = i.name

                    if self.asignaturas_reprobadas:
                        aux_materias_eliminar = self.verificar_horario(ciclo_siguiente2.id, asig_segunda_aux[0][4])
                        aux_materias_eliminar2 = self.verificar_horario_uni(ciclo_anterior2.id, asig_segunda_aux[0][4],asig_tercera_aux[0][4])
                        aux_materias_eliminar3 = self.verificar_horario_bajo(ciclo_siguiente2.id, asig_segunda_aux[0][4], asig_segunda_aux[0][4])
                        for j in self.asignaturas_reprobadas:
                            if j.creditos < (ciclo_siguiente2.creditos*0.2) and j.creditos > asig_mayor_cred_2 and j.name not in aux_materias_eliminar2 and j.name not in aux_materias_eliminar3:
                                asig_mayor_cred_2 = j.creditos
                                asig_mayor_nombre_2 = j.name
                        
                    if self.asignaturas_pendientes:
                        aux_materias_eliminar = self.verificar_horario(ciclo_siguiente2.id, asig_segunda_aux[0][4])
                        aux_materias_eliminar2 = self.verificar_horario_uni(ciclo_siguiente2.id, asig_tercera_aux[0][4],asig_primera_aux[0][4])
                        aux_materias_eliminar3 = self.verificar_horario_bajo(ciclo_siguiente2.id, asig_tercera_aux[0][4], asig_primera_aux[0][3])
                        for j in self.asignaturas_pendientes:
                            if j.creditos < (ciclo_siguiente2.creditos*0.2) and j.creditos > asig_mayor_cred_1 and j.name not in aux_materias_eliminar2 and j.name not in aux_materias_eliminar3:
                                asig_mayor_cred_1 = j.creditos
                                asig_mayor_nombre_1 = j.name
                                #raise ValidationError(aux_materias_eliminar2 + "" + aux_materias_eliminar+ "" + aux_materias_eliminar3)
                    if asig_mayor_nombre_1 != "" and asig_mayor_nombre_2 != "":
                        asig_mayor_nombre_1= ""
                    
                    self.asignaturas_tercera = asig_mayor_nombre_3
                    self.asignaturas_segunda = asig_mayor_nombre_2
                    self.asignaturas_primera = asig_mayor_nombre_1
        

        ##########################################

        #caso tres 0 segunda y 1 o 2 en pendientes
        if (len(asig_primera_aux) == 2 or len(asig_primera_aux) == 1) and len(asig_segunda_aux) == 0 and len(asig_tercera_aux) == 0:
            if self.matricular_mismo_ciclo == False:
                suma_creditos = 0

                num_asig_aux = int(self.ciclo_matricular_especial.n_asignaturas)
                sesentaxciento_materias = round(int(num_asig_aux) * 0.6)

                creditos_aux = int(self.ciclo_matricular_especial.creditos)
                creditos = round(creditos_aux * 0.6)

                asignaturas_ciclo_siguiente2 = self.env['ma.asignatura'].search(
                    [('ciclo_id', '=', int(self.ciclo_matricular_especial.id))])
                name_asig = ""
                name_asig_correcto = ""
                for amayor in asignaturas_ciclo_siguiente2:
                    for i in range(len(asig_primera_aux)):

                        aux_materias_eliminar = self.verificar_horario_caso3(int(self.ciclo_matricular_especial.id), asig_primera_aux[i][4])

                        if aux_materias_eliminar != None:
                            name_asig = str(name_asig) + ", " + str(aux_materias_eliminar)
                        for prerre in amayor.prerrequisitos:
                            if str(prerre._origin.name) == str(asig_primera_aux[i][2]):
                                aux_prerre = amayor.name + ", "
                                name_asig = name_asig + aux_prerre

                    if not(amayor.name in name_asig):
                        suma_creditos = suma_creditos + amayor.creditos
                        creditos_asig.append(amayor.creditos)
                        aux_prerre_si = amayor.name + ", "
                        name_asig_correcto = name_asig_correcto + aux_prerre_si

                materias_si = name_asig_correcto.split(sep=', ')
                for x in range(len(materias_si)):
                    if not materias_si[x]:
                        materias_si.pop(x)

                materias_add = ""

                for i in range(3):

                    if suma_creditos > creditos:
                        aux = len(materias_si)
                        aux_menor = 500
                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                
                                aux = x
                                aux_menor = creditos_asig[x]

                        suma_creditos = suma_creditos - creditos_asig[aux]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                # aqui
                for i in range(3):
                    aux = 20
                    aux_menor = 500
                    if len(materias_si) > sesentaxciento_materias:

                        for x in range(len(materias_si)):
                            if creditos_asig[x] < aux_menor:
                                aux = x
                                aux_menor = creditos_asig[x]
                        materias_si.pop(aux)
                        creditos_asig.pop(aux)

                for i in range(len(materias_si)):
                    materias_add = materias_add + materias_si[i] + ","

                materias_add = materias_add.replace(',,', '')
                add = ""
                for i in range(len(asig_primera_aux)):
                    add = add + asig_primera_aux[i][2] + ","
                self.asignaturas_primera = materias_add + add
                self.ciclo_matricular = ciclo_siguiente2.name

            aux_reporte_horario = aux_materias_eliminar + aux_materias_eliminar2 + aux_materias_eliminar3
            aux_reporte_horario = aux_reporte_horario.strip()
            aux_reporte_horario = aux_reporte_horario.replace(",,,", ",")
            aux_reporte_horario = aux_reporte_horario.replace(",,", ",")
            aux_list_horario = aux_reporte_horario.split(",")
            aux_list_horario1 = set(aux_list_horario)

            if self.matricular_mismo_ciclo == True:
                self.ciclo_matricular = self.ciclo_materias_pendientes.name
            else:
                self.ciclo_matricular = self.ciclo_matricular_especial.name

            self.valores_pagar = ""
            self.asignaturas_tercera = ""
            self.asignaturas_segunda = ""
            aux_quitar = self.asignaturas_primera
            texto_sin_comas = aux_quitar.replace(",,", ",")
            mensaje = texto_sin_comas.replace(",,", " ")
            mensaje = mensaje[:-1]

        valor = ""
        if self.calcular_valores:
            valor = self.calcularValores(total_creditos_tercera, total_creditos_segunda)
        self.valores_pagar = valor

    def calcularValores(self, total_creditos_tercera, total_creditos_segunda):
        valor = 0
        n_horas = self.carrera_id.duracion_horas
        n_ciclos = self.carrera_id.numero_ciclos
        costo_optimo_anual = self.costo_optimo_id.valor
        arancel = self.grupo_socioeconomico_id.arancel
        arancel = arancel/100
        matricula = self.grupo_socioeconomico_id.matricula
        matricula = matricula/100
        aux_tercera = total_creditos_tercera
        factorA = aux_tercera + total_creditos_segunda
        factorB = (n_horas/n_ciclos)*2
        factorC = costo_optimo_anual
        factorD = factorC/factorB
        factorE = factorD*factorA
        factorF = arancel
        factorG = factorE * factorF
        factorH = factorB/2
        factorI = factorD * factorH
        factorJ = matricula
        factorK = factorI*factorJ
        valor = factorG + factorK
        valor = round(valor,2)
        return valor
    
    def verificar_horario(self, id_ciclo_matricular, reprobadas_id):
        error_horario = []
        if len(self.asignaturas_reprobadas_tercera)>0:
            paralelo_anterior = self.paralelo_ciclo_reprobar_tercera
        else:
            paralelo_anterior = self.paralelo_ciclo_reprobar

        paralelo_matricular = self.env['ma.paralelo'].search(
            [('name', '=', paralelo_anterior.name), ('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)])


        if paralelo_matricular.name == False:
            paralelo_matricular = self.env['ma.paralelo'].search(
                [('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)], limit=1)
        
        # Horario Inicio
        for pa_lunes in paralelo_anterior.horario_lunes:
            for pm_lunes in paralelo_matricular.horario_lunes:
                if pa_lunes.asignatura_id.id == reprobadas_id and pa_lunes.numero_hora == pm_lunes.numero_hora \
                        and pm_lunes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_lunes.asignatura_id.name)
        for pa_martes in paralelo_anterior.horario_martes:
            for pm_martes in paralelo_matricular.horario_martes:
                if pa_martes.asignatura_id.id == reprobadas_id and pa_martes.numero_hora == pm_martes.numero_hora \
                        and pm_martes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_martes.asignatura_id.name)
        for pa_miercoles in paralelo_anterior.horario_miercoles:
            for pm_miercoles in paralelo_matricular.horario_miercoles:
                if pa_miercoles.asignatura_id.id == reprobadas_id and pa_miercoles.numero_hora == pm_miercoles.numero_hora \
                        and pm_miercoles.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_miercoles.asignatura_id.name)
        for pa_jueves in paralelo_anterior.horario_jueves:
            for pm_jueves in paralelo_matricular.horario_jueves:
                if pa_jueves.asignatura_id.id == reprobadas_id and pa_jueves.numero_hora == pm_jueves.numero_hora \
                        and pm_jueves.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_jueves.asignatura_id.name)
        for pa_viernes in paralelo_anterior.horario_viernes:
            for pm_viernes in paralelo_matricular.horario_viernes:
                if pa_viernes.asignatura_id.id == reprobadas_id and pa_viernes.numero_hora == pm_viernes.numero_hora \
                        and pm_viernes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_viernes.asignatura_id.name)
        
        # Horario Fin
        resultantList = ""
        if error_horario:
            resultantList = ""
            for element in error_horario:
                if element not in resultantList:
                    resultantList = resultantList + "," + str(element)

        return resultantList

    def verificar_horario_caso3(self, id_ciclo_matricular, reprobadas_id):

        error_horario = []
        id_ciclo = self.ciclo_materias_pendientes
        paralelo_anterior = self.env['ma.paralelo'].search(
            [('ciclo_id', '=', int(id_ciclo)), ('periodo_id.estado', '=', True)], limit=1)

        paralelo_matricular = self.env['ma.paralelo'].search(
            [('name', '=', paralelo_anterior.name), ('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)])

        if paralelo_matricular.name == False:
            paralelo_matricular = self.env['ma.paralelo'].search(
                [('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)], limit=1)
        
        # Horario Inicio
        for pa_lunes in paralelo_anterior.horario_lunes:
            for pm_lunes in paralelo_matricular.horario_lunes:
                if pa_lunes.asignatura_id.id == reprobadas_id and pa_lunes.numero_hora == pm_lunes.numero_hora \
                        and pm_lunes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_lunes.asignatura_id.name)
        for pa_martes in paralelo_anterior.horario_martes:
            for pm_martes in paralelo_matricular.horario_martes:
                if pa_martes.asignatura_id.id == reprobadas_id and pa_martes.numero_hora == pm_martes.numero_hora \
                        and pm_martes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_martes.asignatura_id.name)
        for pa_miercoles in paralelo_anterior.horario_miercoles:
            for pm_miercoles in paralelo_matricular.horario_miercoles:
                if pa_miercoles.asignatura_id.id == reprobadas_id and pa_miercoles.numero_hora == pm_miercoles.numero_hora \
                        and pm_miercoles.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_miercoles.asignatura_id.name)
        for pa_jueves in paralelo_anterior.horario_jueves:
            for pm_jueves in paralelo_matricular.horario_jueves:
                if pa_jueves.asignatura_id.id == reprobadas_id and pa_jueves.numero_hora == pm_jueves.numero_hora \
                        and pm_jueves.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_jueves.asignatura_id.name)
        for pa_viernes in paralelo_anterior.horario_viernes:
            for pm_viernes in paralelo_matricular.horario_viernes:
                if pa_viernes.asignatura_id.id == reprobadas_id and pa_viernes.numero_hora == pm_viernes.numero_hora \
                        and pm_viernes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_viernes.asignatura_id.name)
        
        # Horario Fin
        resultantList = ""
        if error_horario:
            resultantList = ""

            for element in error_horario:
                if element not in resultantList:
                    resultantList = resultantList + "," + str(element)

        return resultantList

    def verificar_horario_bajo(self, id_ciclo_matricular, reprobadas_id, ciclo):

        error_horario = []
        paralelo_anterior = self.env['ma.paralelo'].search(
            [('ciclo_id', '=', int(ciclo)), ('periodo_id.estado', '=', True)], limit=1)

        paralelo_matricular = self.env['ma.paralelo'].search(
            [('name', '=', paralelo_anterior.name), ('ciclo_id', '=', id_ciclo_matricular)], limit=1)

        if paralelo_matricular.name == False:
            paralelo_matricular = self.env['ma.paralelo'].search(
                [('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)], limit=1)
       
        # Horario Inicio
        for pa_lunes in paralelo_anterior.horario_lunes:
            for pm_lunes in paralelo_matricular.horario_lunes:

                if pa_lunes.asignatura_id.id == reprobadas_id and pa_lunes.numero_hora == pm_lunes.numero_hora \
                        and pm_lunes.ciclo_id.id == id_ciclo_matricular:

                    error_horario.append(pm_lunes.asignatura_id.name)
        for pa_martes in paralelo_anterior.horario_martes:
            for pm_martes in paralelo_matricular.horario_martes:
                if pa_martes.asignatura_id.id == reprobadas_id and pa_martes.numero_hora == pm_martes.numero_hora \
                        and pm_martes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_martes.asignatura_id.name)
        for pa_miercoles in paralelo_anterior.horario_miercoles:
            for pm_miercoles in paralelo_matricular.horario_miercoles:
                if pa_miercoles.asignatura_id.id == reprobadas_id and pa_miercoles.numero_hora == pm_miercoles.numero_hora \
                        and pm_miercoles.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_miercoles.asignatura_id.name)
        for pa_jueves in paralelo_anterior.horario_jueves:
            for pm_jueves in paralelo_matricular.horario_jueves:
                if pa_jueves.asignatura_id.id == reprobadas_id and pa_jueves.numero_hora == pm_jueves.numero_hora \
                        and pm_jueves.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_jueves.asignatura_id.name)
        for pa_viernes in paralelo_anterior.horario_viernes:
            for pm_viernes in paralelo_matricular.horario_viernes:
                if pa_viernes.asignatura_id.id == reprobadas_id and pa_viernes.numero_hora == pm_viernes.numero_hora \
                        and pm_viernes.ciclo_id.id == id_ciclo_matricular:
                    error_horario.append(pm_viernes.asignatura_id.name)
        
        # Horario Fin
        resultantList = ""
        if error_horario:
            resultantList = ""

            for element in error_horario:
                if not  str(element) in resultantList:
                    resultantList = resultantList + "," + str(element)

        return resultantList

    def verificar_horario_uni(self, id_ciclo_matricular, reprobadas_id, primera_id):
        error_horario = []
        if len(self.asignaturas_reprobadas_tercera)>0:
            paralelo_anterior = self.paralelo_ciclo_reprobar_tercera
        else:
            paralelo_anterior = self.paralelo_ciclo_reprobar

        paralelo_matricular = self.env['ma.paralelo'].search(
            [('name', '=', paralelo_anterior.name), ('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True)])

        if paralelo_matricular.name == False:
            paralelo_matricular = self.env['ma.paralelo'].search(
                [('ciclo_id', '=', id_ciclo_matricular), ('periodo_id.estado', '=', True) ], limit=1)

        for pa_lunes in paralelo_anterior.horario_lunes:

            for pm_lunes in paralelo_matricular.horario_lunes:

                if pa_lunes.asignatura_id.id == primera_id and pm_lunes.asignatura_id.id == reprobadas_id and pa_lunes.numero_hora == pm_lunes.numero_hora:

                    error_horario.append(pa_lunes.asignatura_id.name)
        
        for pa_martes in paralelo_anterior.horario_martes:
            
            for pm_martes in paralelo_matricular.horario_martes:

                if pa_martes.asignatura_id.id == primera_id and pm_martes.asignatura_id.id == reprobadas_id and pa_martes.numero_hora == pm_martes.numero_hora:

                    error_horario.append(pa_martes.asignatura_id.name)
        for pa_miercoles in paralelo_anterior.horario_miercoles:

            for pm_miercoles in paralelo_matricular.horario_miercoles:

                if pa_miercoles.asignatura_id.id == primera_id and pm_miercoles.asignatura_id.id == reprobadas_id and pa_miercoles.numero_hora == pm_miercoles.numero_hora:

                    error_horario.append(pa_miercoles.asignatura_id.name)

        for pa_jueves in paralelo_anterior.horario_jueves:

            for pm_jueves in paralelo_matricular.horario_jueves:

                if pa_jueves.asignatura_id.id == primera_id and pm_jueves.asignatura_id.id == reprobadas_id and pa_jueves.numero_hora == pm_jueves.numero_hora:

                    error_horario.append(pa_jueves.asignatura_id.name)
        for pa_viernes in paralelo_anterior.horario_viernes:

            for pm_viernes in paralelo_matricular.horario_viernes:

                if pa_viernes.asignatura_id.id == primera_id and pm_viernes.asignatura_id.id == reprobadas_id and pa_viernes.numero_hora == pm_viernes.numero_hora:

                    error_horario.append(pa_viernes.asignatura_id.name)
        
        # Horario Fin
        resultantList = ""

        if error_horario:
            resultantList = ""
            for element in error_horario:
                if not element in resultantList:
                    resultantList = resultantList + "," + str(element)
        return resultantList


    @api.onchange('asignaturas_pendientes','asignaturas_reprobadas','asignaturas_reprobadas_tercera')
    def validar_primera_matricula(self):
        print("Entra")
        asig_primera_aux = []
        for asig_primera in self.asignaturas_pendientes:
            for asig_reprobadas in self.asignaturas_reprobadas:
                if asig_primera.id == asig_reprobadas.id:
                    raise ValidationError("Usted no puede seleccionar las mismas asignaturas")

        for asig_primera in self.asignaturas_pendientes:
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_primera.ciclo_id.name))]
            aux1 = int(aux[0])
            dato2 = [aux1, str(asig_primera.ciclo_id.name), str(asig_primera.name), str(asig_primera.ciclo_id.id)]
            asig_primera_aux.append(dato2)
        #validar primera
        if not self.asignaturas_reprobadas_tercera and not self.asignaturas_reprobadas and self.asignaturas_pendientes:
            print("Entra")
            if len(asig_primera_aux) <= 2:
                print("Entra")
                self.validar_matricula_1_2 = True
            else:
                self.validar_matricula_1_2 = False
        else:
            self.validar_matricula_1_2 = False

    def aprobar_solicitud(self):
        self.solicitud_aprobado = True

    def rechazar_solicitud(self):
        self.solicitud_rechazada = True
        error = False
        try:
            template_rec = self.env.ref('modulo_matriculas.email_template_notificar_solicitud_rechazada')
            template_rec.write({'email_to': self.user_id.email})
            template_rec.send_mail(self.id, force_send=True)
        except:
            error = True

        if error==True:
            self.env.user.notify_danger(message='Se produjo un error al enviar la Notificación al correo electrónico')

class Asignatura(models.Model):
    _name = "ma.asignatura"
    _description = "Asignaturas"
    name = fields.Char(string="Nombre de la asignatura", required=True)
    creditos = fields.Integer(string="Créditos/Horas")
    carrera_id = fields.Many2one(
        "ma.carrera", string="Carrera",
        default=lambda self: self.env['ma.carrera'].search([], limit=1),
        ondelete="cascade")

    ciclo_id = fields.Many2one("ma.ciclo", string="Ciclo")

    prerrequisitos = fields.Many2many(
        'ma.asignatura', 'ma_asignaturapre_rel',
        'asignatura_id', 'ciclo_id', string='Prerrequisitos')

    matricula_id = fields.Many2one("ma.matricula", string="Matricula", ondelete="cascade")
    @api.model
    def create(self, vals):
        usuario = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        if usuario.has_group('modulo_matriculas.res_groups_alumnos'):
            raise ValidationError("Usted no puede crear Asignaturas")
        else:
            return super(Asignatura, self).create(vals)

    @api.constrains('ciclo_id')
    def _validarNMaterias(self):
        asignaturas = self.env['ma.asignatura'].search([('ciclo_id', '=', self.ciclo_id.id)])
        if len(asignaturas) > self.ciclo_id.n_asignaturas:
            raise ValidationError(
                "Ha excedido el número de materias en el ciclo, por favor modificar número de materias en: \nDatos Carrera >> Ciclo")

    @api.constrains('ciclo_id', 'creditos')
    def _validarNCreditos(self):
        asignaturas = self.env['ma.asignatura'].search([('ciclo_id', '=', self.ciclo_id.id)])
        creditos = 0
        for asignatura in asignaturas:
            creditos = creditos + asignatura.creditos
        if creditos > self.ciclo_id.creditos:
            raise ValidationError(
                "Ha excedido el número de créditos en el ciclo, por favor modificar número de créditos en: \nDatos Carrera >> Ciclo")

class Periodomatricula(models.Model):
    _name = "ma.periodomatricula"
    _description = "Periódo de Matrículas"

    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El nombre del Periodo ya existe!"),
    ]

    name = fields.Char(string="Nombre del Periodo de Matrículas")
    fecha_inicio = fields.Date(string="Fecha de inicio")
    fecha_fin = fields.Date(string="Fecha de fin")
    estado = fields.Boolean(string="Estado", default=True)

    def botonmatricularse(self):
        return {
            'name': 'Matriculas',
            'type': 'ir.actions.act_window',
            'res_model': 'ma.matricula',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'self'
        }

    @api.constrains('fecha_inicio')
    def _validarEstadoMatricula_inicio(self):
        today = fields.Date.today()
        if self.fecha_inicio <= today:
            self.estado = True
        else:
            self.estado = False

    @api.constrains('fecha_fin')
    def _validarEstadoMatricula_fin(self):
        today = fields.Date.today()
        if self.fecha_fin <= today:
            self.estado = False
        else:
            self.estado = True

    def validarInicioMatricula(self):
        periodos = self.env['ma.periodomatricula'].search([('estado', '=', False)])
        today = fields.Date.today()
        for periodo in periodos:
            if today >= periodo.fecha_inicio:
                periodo.estado = True


class Ciclo(models.Model):
    _name = "ma.ciclo"
    _description = " Ciclos"
    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El nombre del ciclo ya existe!"),
    ]

    name = fields.Char(string="Nombre del ciclo")
    nombre_ciclo = fields.Char(string="Nombre del ciclo", required=True)
    creditos = fields.Integer(string="Créditos")
    n_asignaturas = fields.Integer(string="Número de Asignaturas")
    numero_ciclo = fields.Selection(
        selection=[("ciclo_1", "1"), ("ciclo_2", "2"), ("ciclo_3", "3"),
                   ("ciclo_4", "4"), ("ciclo_5", "5"), ("ciclo_6", "6"),
                   ("ciclo_7", "7"), ("ciclo_8", "8"), ("ciclo_9", "9"), ("ciclo_10", "10")],
        string="Ciclo", required=True)
    carrera_id = fields.Many2one("ma.carrera", string="Carrera")

    paralelo_ids = fields.One2many("ma.paralelo", "ciclo_id",
                                   string="Paralelos")

    @api.constrains('nombre_ciclo')
    def crearNombre(self):
        nombre_ciclo = self.nombre_ciclo
        numero_ciclo = self.numero_ciclo
        self.name = str(numero_ciclo)[6:] + "." + str(nombre_ciclo)

class Paralelo(models.Model):
    _name = "ma.paralelo"
    _description = " Paralelos"

    name = fields.Char(string="Paralelo")
    horario_lunes = fields.One2many("ma.horario", "paralelo_id1",
                                    string="Lunes")
    horario_martes = fields.One2many("ma.horario", "paralelo_id2",
                                     string="Martes")
    horario_miercoles = fields.One2many("ma.horario", "paralelo_id3",
                                        string="Miércoles")
    horario_jueves = fields.One2many("ma.horario", "paralelo_id4",
                                     string="Jueves")
    horario_viernes = fields.One2many("ma.horario", "paralelo_id5",
                                      string="Viernes")

    carrera_id = fields.Many2one(
        "ma.carrera", string="Carrera",
        default=lambda self: self.env['ma.carrera'].search([], limit=1),
        ondelete="cascade")

    periodo_id = fields.Many2one(
        "ma.periodomatricula", string="Periodo Matrícula",
        default=lambda self: self.env['ma.periodomatricula'].search([], limit=1),
        ondelete="cascade")

    ciclo_id = fields.Many2one("ma.ciclo", string="Ciclo",
                               default=lambda self: self._origin.id,
                               ondelete="cascade")

class Horario(models.Model):
    _name = "ma.horario"
    _description = " Horario"

    numero_hora = fields.Selection(
        selection=[("1", "1ra"), ("2", "2da"), ("3", "3ra"),
                   ("4", "4ta"), ("5", "5ta"), ("6", "6ta"),
                   ("7", "7ma"), ("8", "8va"), ("9", "9na"),
                   ("10", "10ma"),("11", "11va"), ("12", "12va")], string="Número de Hora", required=True)

    asignatura_id = fields.Many2one(
        "ma.asignatura", string="Asignatura")

    paralelo_id1 = fields.Many2one("ma.paralelo", string="Paralelo",
                                   default=lambda self: self._origin.id,
                                   ondelete="cascade")
    paralelo_id2 = fields.Many2one("ma.paralelo", string="Paralelo",
                                   default=lambda self: self._origin.id,
                                   ondelete="cascade")
    paralelo_id3 = fields.Many2one("ma.paralelo", string="Paralelo",
                                   default=lambda self: self._origin.id,
                                   ondelete="cascade")
    paralelo_id4 = fields.Many2one("ma.paralelo", string="Paralelo",
                                   default=lambda self: self._origin.id,
                                   ondelete="cascade")
    paralelo_id5 = fields.Many2one("ma.paralelo", string="Paralelo",
                                   default=lambda self: self._origin.id,
                                   ondelete="cascade")

    carrera_id = fields.Many2one("ma.carrera", string="Carrera",
                                 ondelete="cascade")
    ciclo_id = fields.Many2one("ma.ciclo", string="Ciclo",
                               ondelete="cascade")

class ResUser(models.Model):
    _inherit = "res.users"
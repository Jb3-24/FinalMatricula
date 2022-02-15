import datetime
import re
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Carrera(models.Model):
    _name = "ma.carrera"
    _description = "Carrera"
    name = fields.Char(string="Nombre de la Carrera", required=True)


class Matricula(models.Model):
    _name = "ma.matricula"
    _description = "Matricula"

    name = string = "Matriculas"
    nombre_alumno = fields.Char(string="Nombre", required=True, default="[Nombre alumno]")
    cedula_alumno = fields.Char(string="Cédula", required=True, default="[Número de cédula]")

    user_id = fields.Many2one(
        "res.users", string="Alumno",
        default=lambda self: self.env.uid,
        ondelete="cascade")

    carrera_id = fields.Many2one(
        "ma.carrera", string="Carrera",
        default=lambda self: self.env['ma.carrera'].search([], limit=1),
        ondelete="cascade")

    
    # tercera matricula datos
    tercera_matricula = fields.Boolean(string="Matricularse en tercera matrícula?", default=False)
    ciclo_materias_reprobadas_tercera = fields.Many2one("ma.ciclo", string="Ciclo en el cual reprobó la materia en tercera matricula")
    asignaturas_reprobadas_tercera = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel3',
        'asignatura_id', 'ciclo_id', string='Asignaturas Reprobadas por Tercera matricula'
    )

    #segunda matricula datos
    segunda_matricula = fields.Boolean(string="Matricularse en segunda matrícula?", default=False)
    ciclo_materias_reprobadas = fields.Many2one("ma.ciclo", string="Ciclo en el cual reprobó asignaturas")
    # Campo para Paralelo y validaciones
    paralelo_ciclo_reprobar = fields.Many2one("ma.paralelo", string="Paralelo del Ciclo en el cual reprobó asignaturas")

    asignaturas_reprobadas = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel2',
        'asignatura_id', 'ciclo_id', string='Asignaturas Reprobadas por Segunda Matricula'
    )

    #datos primera matricula
    primera_matricula = fields.Boolean(string="Matricularse en primera matrícula?", default=False)
    ciclo_materias_pendientes = fields.Many2one("ma.ciclo", string="Ciclo en el cual tiene materias pendientes")
    asignaturas_pendientes = fields.Many2many(
        'ma.asignatura', 'ma_asignaturarep_rel1',
        'asignatura_id', 'ciclo_id', string='Asignaturas Pendientes'
    )

    #Campo para ciclo a matrícular
    #Campo para guardar la respuesta luego de aplicar las normas de la U

    asignaturas_tercera = fields.Char(string="Materias matricular 3")
    asignaturas_segunda = fields.Char(string="Materias matricular 2")
    asignaturas_primera = fields.Char(string="Materias matricular 1")
    ciclo_matricular = fields.Char(string="Ciclo en el que se va a matricular")




    def botonmatricular(self):

        #tercera matricula
        asig_tercera_aux = []
        for asig_tercera in self.asignaturas_reprobadas_tercera:
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_tercera.ciclo_id.name))]
            aux1 = int(aux[0])
            dato = [aux1,str(asig_tercera.ciclo_id.name),str(asig_tercera.name)]
            asig_tercera_aux.append(dato)

        asig_tercera_aux_ordenada = sorted(asig_tercera_aux, key=lambda x: x[0])
        self.ciclo_matricular = asig_tercera_aux_ordenada[0][1]
        self.asignaturas_tercera = asig_tercera_aux_ordenada[0][2]

        #segunda matricula
        asig_segunda_aux = []
        for asig_segunda in self.asignaturas_reprobadas:
            aux = [int(s) for s in re.findall(r'-?\d\d*', str(asig_segunda.ciclo_id.name))]
            aux1 = int(aux[0])
            dato2 = [aux1, str(asig_segunda.ciclo_id.name), str(asig_segunda.name), str(asig_segunda.ciclo_id.id)]
            asig_segunda_aux.append(dato2)
            


        asig_segunda_aux_ordenada = sorted(asig_segunda_aux, key=lambda x: x[0])
        asig_segunda_aux_ordenada_des = sorted(asig_segunda_aux, key=lambda x: x[0], reverse=True)
        self.ciclo_matricular = asig_segunda_aux_ordenada[0][1]
        #materias2_concatenar = asig_segunda_aux_ordenada[0][2] +", "+ asig_segunda_aux_ordenada[1][2]
        #self.asignaturas_segunda = materias2_concatenar

        ciclo_mayor = asig_segunda_aux_ordenada_des[0][0]
        id_ciclo = asig_segunda_aux_ordenada_des[0][3]
        ciclo = self.env['ma.ciclo'].search(
            [('id', '=', id_ciclo)])

        n_asignaturas = ciclo.n_asignaturas
        n_asignaturas = round(n_asignaturas * 0.40)
        print(n_asignaturas)
        c = 0
        s = ""
        for i in range(len(asig_segunda_aux_ordenada_des)):

            if asig_segunda_aux_ordenada_des[i][0] == ciclo_mayor:

                c += 1
                if c > n_asignaturas:
                    asig_segunda_aux_ordenada_des[i] = ["","",""]

            aux = asig_segunda_aux_ordenada_des[i][2]
            s = s + str(aux) + ", "
        self.asignaturas_segunda = s
        self.ciclo_matricular = ciclo_mayor







        


    def _modificarCiclos(self):
        self._materiasMatricula()
        contador = 0
        ciclo_reprobado = self.ciclo_materias_reprobadas
        numero_asignaturas = ciclo_reprobado.n_asignaturas
        n_materias_matricular = round(numero_asignaturas * 0.40)
        tipo_matri = "Tipo Matrícula"
        for record in self.asignaturas_reprobadas:
            contador = contador + 1
        if contador > 1 and tipo_matri == "tercera_matricula":
            raise ValidationError("No puedes seleccionar mas de una materias")
        elif contador > n_materias_matricular and tipo_matri == "segunda_matricula":
            raise ValidationError("No puedes seleccionar mas del 40% de materias")



    def _materiasMatricula(self):

        creditos = self.ciclo_materias_matricular.creditos
        ciclo_matricular = self.ciclo_materias_matricular
        paralelo_anterior = self.paralelo_ciclo_reprobar
        creditos = round(creditos * 0.60)
        asignaturas_no = ""
        error_cadena = ""
        error_creditos = ""
        error_horario = []
        creditos_suma = 0

        paralelo_matricular = self.env['ma.paralelo'].search(
            [('name', '=', paralelo_anterior.name), ('ciclo_id', '=', ciclo_matricular.id)])

        if paralelo_matricular.name == False:
            paralelo_matricular = self.env['ma.paralelo'].search(
                [('ciclo_id', '=', ciclo_matricular.id)], limit=1)

        print(paralelo_matricular.name)
        print(ciclo_matricular.id)
        for matricular in self.ciclo_materias_matricular:
            creditos_suma = creditos_suma + matricular.creditos
            for reprobadas in self.asignaturas_reprobadas:
                # Horario Inicio
                for pa_lunes in paralelo_anterior.horario_lunes:
                    for pm_lunes in paralelo_matricular.horario_lunes:
                        if pa_lunes.asignatura_id.id == reprobadas._origin.id and pa_lunes.numero_hora == pm_lunes.numero_hora \
                                and pm_lunes.asignatura_id.id == matricular._origin.id:
                            error_horario.append(pm_lunes.asignatura_id.name)
                for pa_martes in paralelo_anterior.horario_martes:
                    for pm_martes in paralelo_matricular.horario_martes:
                        if pa_martes.asignatura_id.id == reprobadas._origin.id and pa_martes.numero_hora == pm_martes.numero_hora \
                                and pm_martes.asignatura_id.id == matricular._origin.id:
                            error_horario.append(pm_martes.asignatura_id.name)
                for pa_miercoles in paralelo_anterior.horario_miercoles:
                    for pm_miercoles in paralelo_matricular.horario_miercoles:
                        if pa_miercoles.asignatura_id.id == reprobadas._origin.id and pa_miercoles.numero_hora == pm_miercoles.numero_hora \
                                and pm_miercoles.asignatura_id.id == matricular._origin.id:
                            error_horario.append(pm_miercoles.asignatura_id.name)
                for pa_jueves in paralelo_anterior.horario_jueves:
                    for pm_jueves in paralelo_matricular.horario_jueves:
                        if pa_jueves.asignatura_id.id == reprobadas._origin.id and pa_jueves.numero_hora == pm_jueves.numero_hora \
                                and pm_jueves.asignatura_id.id == matricular._origin.id:
                            error_horario.append(pm_jueves.asignatura_id.name)
                for pa_viernes in paralelo_anterior.horario_viernes:
                    for pm_viernes in paralelo_matricular.horario_viernes:
                        if pa_viernes.asignatura_id.id == reprobadas._origin.id and pa_viernes.numero_hora == pm_viernes.numero_hora \
                                and pm_viernes.asignatura_id.id == matricular._origin.id:
                            error_horario.append(pm_viernes.asignatura_id.name)
                # Horario Fin
                for prerre in matricular.prerrequisitos:
                    if prerre._origin.id == reprobadas._origin.id:
                        asignaturas_no = asignaturas_no + reprobadas.name + '; '
                        error_cadena = "Las siguientes asignaturas son cadena: "
        if creditos_suma > creditos:
            error_creditos = "Has superado el nivel de créditos u horas, selecciona nuevamente. \n" + \
                             "Puedes elegir " + str(creditos) + " Créditos u Horas"
        if error_cadena:
            raise ValidationError(error_cadena + asignaturas_no)
        elif error_creditos:
            raise ValidationError(error_creditos)
        elif error_horario:
            resultantList = []

            for element in error_horario:
                if element not in resultantList:
                    resultantList.append(element)
            raise ValidationError(
                "No puede matricularse a las siguientes materias por temas de horarios: " + str(resultantList))



    @api.model
    def create(self, vals):
        matricula = self.env['ma.matricula'].search([('user_id', '=', self.env.uid)], limit=1)
        if matricula:
            raise ValidationError("Usted solo puede crear una matrícula")
        else:
            return super(Matricula, self).create(vals)




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
        'asignatura_id', 'ciclo_id', string='Prerrequisitos'
    )

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

    ciclo_id = fields.Many2one("ma.ciclo", string="Ciclo",
                               default=lambda self: self._origin.id,
                               ondelete="cascade")


class Horario(models.Model):
    _name = "ma.horario"
    _description = " Horario"

    numero_hora = fields.Selection(
        selection=[("1", "1ra"), ("2", "2da"), ("3", "3ra"),
                   ("4", "4ta"), ("5", "5ta"), ("6", "6ta"),
                   ("7", "7ma"), ("8", "8va"), ("9", "9na"), ("10", "10ma")], string="Número de Hora", required=True)

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

    @api.constrains('vat')
    def _validarCedula(self):

        try:
            nocero = self.vat.strip("0")
            cedula = int(nocero, 0)
        except:
            raise ValidationError("Verifique el número de cédula")
        # sin ceros a la izquierda

        verificador = cedula % 10
        numero = cedula // 10

        # mientras tenga números
        suma = 0
        while (numero > 0):

            # posición impar
            posimpar = numero % 10
            numero = numero // 10
            posimpar = 2 * posimpar
            if (posimpar > 9):
                posimpar = posimpar - 9

            # posición par
            pospar = numero % 10
            numero = numero // 10

            suma = suma + posimpar + pospar

        decenasup = suma // 10 + 1
        calculado = decenasup * 10 - suma
        if (calculado >= 10):
            calculado = calculado - 10

        if (calculado != verificador):
            raise ValidationError("Verifique el número de cédula")

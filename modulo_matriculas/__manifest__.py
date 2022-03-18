{
    "name": "Simulación de matrículas en la Carrera de Ingeniería en Sistemas",
    "description": "Módulo de software para la simulación de matrícula por asignatura en la carrera de Ingeniería en Sistemas de la Universidad Nacional de Loja",
    "author": "Johnney Bermeo",

    "summary": """
        Módulo de software para la simulación de matrícula por asignatura en la carrera de Ingeniería en Sistemas de la Universidad Nacional de Loja
        """,

    "website": "https://unl.edu.ec/",

    "category": "Matricula",

    "version": "1.0",
    "depends": ["base", "mail"],
    "data": [
        "data/quotation_expiration_cron.xml",
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "views/views.xml",
        "report/template.xml",
        "report/report.xml"
    ]
}
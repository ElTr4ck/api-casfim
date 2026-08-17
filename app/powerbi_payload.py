"""Payload base para las consultas al reporte de SOFOMERs en PowerBI.

INSTRUCCIONES
-------------
1. Abre las DevTools del navegador (F12) → pestaña Network.
2. Navega al reporte PowerBI y aplica uno de los filtros de grupo.
3. Busca la petición POST a `querydata?synchronous=true`.
4. Copia el Request Body completo (JSON) y pégalo como valor de PAYLOAD.
5. Guarda este archivo. La API detectará automáticamente el campo correcto del
   filtro de Grupo y lo sobreescribirá en cada llamada.

El payload se modifica en tiempo de ejecución: nunca es necesario cambiarlo
manualmente para alternar entre "consolidan" y "no consolidan".
"""

# ---------------------------------------------------------
# ↓↓  PEGA AQUÍ EL JSON DEL REQUEST PAYLOAD DE POWER BI  ↓↓
# ---------------------------------------------------------
PAYLOAD: dict = {
    "version": "1.0.0",
    "queries": [
        {
            "Query": {
                "Commands": [
                    {
                        "SemanticQueryDataShapeCommand": {
                            "Query": {
                                "Version": 2,
                                "From": [
                                    {
                                        "Name": "l",
                                        "Entity": "LT_Instituciones",
                                        "Type": 0
                                    },
                                    {
                                        "Name": "f",
                                        "Entity": "FT_situacion_Financiera",
                                        "Type": 0
                                    },
                                    {
                                        "Name": "l1",
                                        "Entity": "LT_Periodos",
                                        "Type": 0
                                    }
                                ],
                                "Select": [
                                    {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": "l"
                                                }
                                            },
                                            "Property": "cve_institucion"
                                        },
                                        "Name": "LT_Instituciones.cve_institucion"
                                    },
                                    {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": "l"
                                                }
                                            },
                                            "Property": "Nombre Institución"
                                        },
                                        "Name": "LT_Instituciones.Nombre Institución"
                                    },
                                    {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": "l"
                                                }
                                            },
                                            "Property": "nombre corto grupo"
                                        },
                                        "Name": "LT_Instituciones.nombre corto grupo"
                                    },
                                    {
                                        "Measure": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": "f"
                                                }
                                            },
                                            "Property": "PeriodoMasAntiguoReportadoInstitucion"
                                        },
                                        "Name": "FT_situacion_Financiera.PeriodoMasAntiguoReportadoInstitucion"
                                    },
                                    {
                                        "Measure": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": "f"
                                                }
                                            },
                                            "Property": "PeriodoMasRecienteReportadoInstitucionesSeleccionadas"
                                        },
                                        "Name": "FT_situacion_Financiera.PeriodoMasRecienteReportadoInstitucionesSeleccionadas"
                                    }
                                ],
                                "Where": [
                                    {
                                        "Condition": {
                                            "In": {
                                                "Expressions": [
                                                    {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "l"
                                                                }
                                                            },
                                                            "Property": "Grupo"
                                                        }
                                                    }
                                                ],
                                                "Values": [
                                                    [
                                                        {
                                                            "Literal": {
                                                                "Value": "'Sofomers que consolidan con bancos'"
                                                            }
                                                        }
                                                    ]
                                                ]
                                            }
                                        }
                                    },
                                    {
                                        "Condition": {
                                            "Not": {
                                                "Expression": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "l"
                                                                        }
                                                                    },
                                                                    "Property": "cve_institucion"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "'31'"
                                                                    }
                                                                }
                                                            ],
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "'32'"
                                                                    }
                                                                }
                                                            ],
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "'33'"
                                                                    }
                                                                }
                                                            ],
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "null"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "Condition": {
                                            "In": {
                                                "Expressions": [
                                                    {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "l1"
                                                                }
                                                            },
                                                            "Property": "SlicerDate"
                                                        }
                                                    }
                                                ],
                                                "Values": [
                                                    [
                                                        {
                                                            "Literal": {
                                                                "Value": "'Periodo mas Reciente'"
                                                            }
                                                        }
                                                    ]
                                                ]
                                            }
                                        }
                                    }
                                ],
                                "OrderBy": [
                                    {
                                        "Direction": 1,
                                        "Expression": {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {
                                                        "Source": "l"
                                                    }
                                                },
                                                "Property": "nombre corto grupo"
                                            }
                                        }
                                    }
                                ]
                            },
                            "Binding": {
                                "Primary": {
                                    "Groupings": [
                                        {
                                            "Projections": [
                                                0,
                                                1,
                                                2,
                                                3,
                                                4
                                            ]
                                        }
                                    ]
                                },
                                "DataReduction": {
                                    "DataVolume": 3,
                                    "Primary": {
                                        "Window": {
                                            "Count": 500
                                        }
                                    }
                                },
                                "Version": 1
                            },
                            "ExecutionMetricsKind": 1
                        }
                    }
                ]
            },
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": "f7aaa3d7-4f6d-419a-9f80-69eab1ab617c",
                "Sources": [
                    {
                        "ReportId": "5d2ea1eb-75fb-469c-84ae-463689c86eca",
                        "VisualId": "c7c2243e9b2cb479921c"
                    }
                ]
            }
        }
    ],
    "cancelQueries": [],
    "modelId": 384824
}
# ---------------------------------------------------------

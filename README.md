# Análisis SACYL

Aplicación local para importar informes PDF de laboratorio, conservar una historia longitudinal en SQLite y explorar series mediante FastAPI, una interfaz web y un wrapper de escritorio pywebview. Conceptualmente, cada base SQLite representa a un paciente.

```text
PDF → parsers → SQLite → FastAPI → frontend web → ECharts
```

ECharts 5.6.0 se distribuye localmente y el servidor escucha únicamente en loopback. Los histogramas RBC, PLT y WBC son proxies visuales: no proceden directamente del analizador y no tienen valor diagnóstico.

## Ejecución básica

El proyecto soporta y prueba Python 3.12. Tras instalar el perfil adecuado:

```bash
python -m app.web_main --browser
python -m app.web_main --desktop
python -m app.web_main --smoke-test
bash run_all_tests.sh
```

Las instrucciones completas de entorno, perfiles y build están en [Entorno y build](docs/ENVIRONMENT_AND_BUILD.md).

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md)
- [Estado técnico actual](docs/CURRENT_STATE.md)
- [Datos y privacidad](docs/DATA_AND_PRIVACY.md)
- [Entorno y build](docs/ENVIRONMENT_AND_BUILD.md)
- [Decisiones](docs/DECISIONS.md)
- [Backlog](docs/BACKLOG.md)
- [Roadmap operativo](docs/ROADMAP_OPERATIVO.md)
- [Reconciliación documental](docs/RECONCILIATION.md)

Los datos clínicos reales, PDFs reales y bases SQLite personales deben permanecer fuera del repositorio y de los artefactos públicos.

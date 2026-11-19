# ☁️ OrderFlow Cloud — Despliegue de Aplicación Web en Alta Disponibilidad

Proyecto de infraestructura en la nube y contenerización con arquitectura de alta disponibilidad, balanceo de cargas, persistencia de datos y seguridad SSL/TLS.

## 🏗️ Arquitectura del Sistema

```text
[Usuario HTTPS] ──► [Dominio DNS] ──► [Nginx Load Balancer + SSL]
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
              [Contenedor App 1]                        [Contenedor App 2]
               (FastAPI Python)                          (FastAPI Python)
                       │                                         │
                       └────────────────────┬────────────────────┘
                                            ▼
                                 [PostgreSQL Database]
                                  (Volumen Persistente)
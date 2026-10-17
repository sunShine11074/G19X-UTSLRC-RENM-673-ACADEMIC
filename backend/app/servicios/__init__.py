"""Servicios de la aplicación: reglas de negocio sobre la base y el motor (§3.9).

No importan FastAPI. Cada servicio que escribe termina con `sesion.commit()`; un error de
dominio deja la transacción sin confirmar y se deshace al cerrar la sesión (§3.2).
"""

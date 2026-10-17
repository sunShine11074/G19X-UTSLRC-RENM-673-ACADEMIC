"""Cuentas, sesión y autorización por propietario (§3.8; §6; WP3).

- `contrasenas`: hash Argon2id y política de contraseña (RNF-04; D-02; D-04).
- `sesion`: cookie firmada con HMAC-SHA256, solo con la biblioteca estándar (D-01).
- `servicio`: aviso vigente, registro, inicio de sesión, revocación y lectura de la cuenta.
- `dependencias`: `usuario_vigente*` y `verificar_origen`; el único módulo de este paquete
  que importa FastAPI (§2).
"""

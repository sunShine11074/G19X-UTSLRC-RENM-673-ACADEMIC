-- Paso 1: se ejecuta conectado a la base 'postgres'.
CREATE DATABASE proyecto077;
CREATE ROLE app_077 WITH LOGIN;
GRANT CONNECT ON DATABASE proyecto077 TO app_077;

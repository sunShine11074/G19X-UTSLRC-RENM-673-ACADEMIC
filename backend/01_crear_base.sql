-- Paso 1: se ejecuta conectado a la base 'postgres'.
CREATE DATABASE proyecto077;
CREATE ROLE app_077 WITH LOGIN PASSWORD '8aKeNpCUxkmL69ncexPT7NWFU5Ba';
GRANT CONNECT ON DATABASE proyecto077 TO app_077;

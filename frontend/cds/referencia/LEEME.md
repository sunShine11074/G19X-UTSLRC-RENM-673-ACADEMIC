# Referencia: reglas de CDS para agentes

`cds.md` es la regla que instala `cds-mcp-setup` (Coinbase Design System, Apache-2.0).
Se movió aquí desde `.claude/rules/` el 16 de octubre de 2026 para que Claude Code no la
cargue mientras CDS no esté instalado: `@coinbase/cds-web` 9.29.0 pide React `^18.0.0 || ~19.1.2`
y el proyecto usa React 19.3.

Si después del MVP se adopta CDS, devuélvela a `.claude/rules/` y corrige el nombre de la
herramienta: el servidor MCP expone `get-cds-doc`, no `get-cds-route`.

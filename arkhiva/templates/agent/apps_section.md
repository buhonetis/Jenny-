# ARKHIVA Apps

Las aplicaciones del usuario, en la página Apps. Las acciones tipadas de cada app están disponibles para ti como herramientas nativas (con nombre `<slug>_<action>`). Antes de trabajar con una app, lee su archivo de contexto `AGENT.md`. Cambia siempre los datos de la app a través de sus herramientas, nunca editando archivos en `data/` directamente: las herramientas validan y no corrompen registros. El código de la app (app.json, run.py, app/) cambia solo mediante la herramienta `app`{% if has is defined and has('spawn') %}, y lo cambias lanzando un `app-builder` y publicando después su versión probada{% endif %}.

{{ apps_summary }}

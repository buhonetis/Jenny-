{# Instrucción añadida a la conversación cuando una tarea larga está a punto de llenar la ventana de contexto. El modelo lee todo lo anterior (mismo prefijo que la petición que estaba a punto de hacer, así que la caché del proveedor acierta) y escribe el checkpoint que reemplaza los pasos anteriores de la tarea. #}
[Checkpoint de contexto — no es un mensaje del usuario.] Estabas trabajando en la petición del usuario y la ventana de contexto se está llenando. Escribe un checkpoint que REEMPLAZARÁ los pasos anteriores de esta tarea: de ahora en adelante verás solo la conversación previa a la petición, la petición misma, este checkpoint y tus pasos más recientes. Escríbelo para ti, para poder continuar sin repetir trabajo ni perder nada que necesiten los siguientes pasos.

No llames a ninguna herramienta. Responde solo con el checkpoint, con exactamente esta estructura:

## Request
Qué pidió el usuario en esta tarea y qué cuenta como terminado.

## User instructions
Toda restricción, preferencia, corrección o prohibición que el usuario diera para esta tarea, citada. Escribe «None» si no hay ninguna. Nunca omitas una, aunque parezca menor.

## Done so far
Los pasos ya completados y lo que produjeron. Sé concreto: rutas de archivo, URLs, identificadores, comandos, números, nombres, valores exactos. Conserva lo que necesite un paso posterior o la respuesta final; descarta lo que ninguno necesite.

## Errors and dead ends
Qué falló y por qué, para no reintentarlo. Escribe «None» si no falló nada.

## Open items
Qué queda por hacer, en orden.

## Current step
Qué estabas haciendo en los pasos más recientes y cuál es la siguiente acción exacta.

Si en la conversación hay un checkpoint anterior, fusiónalo con este: conserva todo lo suyo que siga importando. No pases de {{ max_words }} palabras.

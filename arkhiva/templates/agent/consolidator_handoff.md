{# Se añade a consolidator_archive.md cuando los mensajes archivados dejan una conversación que sigue (compactación por longitud o por inactividad, no /new). Los hechos van a la memoria a largo plazo; el estado de trabajo vuelve solo al prompt de los siguientes turnos. #}
Esta vez tu respuesta tiene dos partes.

Primero, los hechos, exactamente como se describen arriba (o `(nothing)`).

Después, una línea que contenga exactamente `### Working state`, seguida de dónde quedó la conversación al final de estos mensajes, para que pueda continuar después de que se eliminen:

- En curso: la tarea o el tema en progreso, y qué cuenta como terminado. Escribe «Nada en curso» si se cerró.
- Pendientes: lo que se prometió, quedó pendiente o espera al usuario, en orden.
- Último paso: qué se hizo al final y cuál es la siguiente acción.
- Referencias: rutas de archivo, nombres, identificadores, números o URLs que necesitarán los siguientes turnos.

El estado de trabajo no es memoria: puede contener detalles temporales que los hechos omiten. Mantenlo por debajo de 200 palabras.{% if previous %} Abajo hay un estado de trabajo anterior: actualízalo, conservando lo que sigue abierto y descartando lo hecho.

Estado de trabajo anterior:
{{ previous }}{% endif %}

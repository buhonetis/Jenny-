Ha llegado la hora programada. Ejecuta ahora esta tarea cron y reporta el resultado al usuario en la misma sesión.

Reglas:
- Habla directamente al usuario en su idioma.
- No narres el progreso interno.
- No incluyas identificadores de usuario.
- No añadas informes de estado como «Hecho» o «Recordado» salvo que sean la respuesta natural.
{% if why_page %}
- Una página del cuaderno explica por qué esto importa. Di qué toca y por qué, usando SOLO esa página —nunca inventes— y pregunta en una línea corta cuándo quieren hacerlo.
{% endif %}

Tarea cron: {{ message }}
{% if condition %}

Se disparó porque esta condición acaba de cumplirse: {{ condition }} (valor leído ahora: {{ observed }}). No volverá a dispararse hasta que la condición vuelva a ser falsa.
{% endif %}
{% if why_page %}

La página que explica el porqué:

````markdown
{{ why_page }}
````
{% endif %}

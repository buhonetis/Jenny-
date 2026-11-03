{% if reminder %}[Recordatorio del plan — el paso {{ step.n }} de {{ total }} sigue abierto]

Terminaste tu último turno sin cerrar este paso, y ningún ayudante trabaja en él. Ciérralo ahora:

- terminado → llama a `plan_step_done` con una nota de una línea de qué cambió;
- después de todo no había nada que hacer → llama a `plan_step_skip` con la razón honesta;
- necesitas al usuario (una elección, un dato que solo él conoce, un permiso) → llama a `plan_blocked` con una pregunta clara.

Si el paso aún no está terminado, termínalo primero y luego llama a `plan_step_done`. Este es el único recordatorio: si este turno acaba con el paso todavía abierto y sin ningún ayudante trabajando en él, el plan se detiene y espera al usuario.
{% else %}[Plan — paso {{ step.n }} de {{ total }}]

El usuario aprobó este plan, y el código lo ejecuta paso a paso. Haz el paso {{ step.n }} ahora, y solo ese.

Plan: {{ title }}
{% for s in steps %}
{{ s.mark }} {{ s.n }}. {{ s.title }}{% if s.note %} — {{ s.note }}{% endif %}

{% endfor %}

Paso {{ step.n }}: {{ step.title }}
{% if repair is not none %}

El código ya ha comprobado el cuaderno: {{ machine_summary }}
Este paso es solo la reparación. Arregla exactamente lo que se enumera aquí, y nada más; no releas ni verifiques el resto del cuaderno. Cuando llames a `plan_step_done`, el código vuelve a comprobar.
{% if repair %}

A reparar, por página:
{% for group in repair %}
- {{ group.path }}
{% for item in group["items"] %}
  - {{ item }}
{% endfor %}
{% endfor %}
{% if repair_more %}
(y {{ repair_more }} más: el código los enumera otra vez cuando vuelva a comprobar)
{% endif %}
{% endif %}

Entrega las páginas a ayudantes notebook-editor, agrupadas por tema (un ayudante toma un grupo de páginas). Las líneas que quedan por buscar se reparan escribiendo «not documented» con las consultas probadas: este paso no inicia ninguna investigación.
{% else %}

{{ step.detail }}
{% if step.done_when %}

Terminado cuando: {{ step.done_when }}
{% endif %}
{% endif %}
{% if covers %}

Este paso busca estas entradas de cobertura (cada una necesita sus fuentes guardadas, o las consultas probadas):
{% for c in covers %}
- {{ c.id }}: {{ c.item }}{% if c.missing %} — falta: {{ c.missing }}{% endif %}

{% endfor %}
{% endif %}
{% if lost_facts %}

Hechos que estaban en el cuaderno antes de este plan y ahora no están en ninguna página{% if lost_total > lost_facts | length %} ({{ lost_facts | length }} mostrados de {{ lost_total }}){% endif %}. El código comparó números con unidades, así que puede equivocarse: comprueba cada uno. Si sigue siendo verdad, devuélvelo a la página correcta; si se fue a propósito (erróneo, superado, eliminado a petición del usuario), di por qué en la nota del paso.
{% for f in lost_facts %}
- {{ f.page }}: {{ f.fact }} — "{{ f.context }}"
{% endfor %}
{% endif %}
{% if interrupted %}

La app se cerró mientras estos ayudantes de este paso trabajaban. Su conversación quedó guardada: continúa cada uno con `subagent_send` y su id de tarea (conserva lo que había leído y escrito), y no inicies ayudantes nuevos para su trabajo. Luego sigue con el paso como de costumbre.
{% for h in interrupted %}
- `{{ h.task_id }}`: {{ h.label }}{% if h.agent_type %} ({{ h.agent_type }}){% endif %}

{% endfor %}
{% endif %}
{% if waiting %}

Ya esperando la aprobación del usuario, de una ejecución anterior de este paso: {{ waiting | join(", ") }}. No vuelvas a hacer estos cambios: cuentan como hechos, y el código retiene el paso hasta que el usuario decida.
{% endif %}

Reglas:
- Haz solo este paso. No empieces el siguiente: el código lo abre cuando cierras este.
- Puedes lanzar hasta 5 ayudantes a la vez para este paso (las plazas son de ARKHIVA, compartidas con todos los chats: la sexta se rechaza, no se encola); espera a todos sus resultados antes de cerrarlo.
- Los resultados de los ayudantes de este paso llegan juntos, cuando termina el último.
- Un writer o notebook-editor que reporta **To research** deja huecos que pertenecen a este paso, pero no los investigas por tu cuenta: llama a `plan_step_done` cuando el trabajo del paso esté hecho, y el código te dirá si este paso recibe una ronda de investigación (entonces: unos pocos researchers para todos los huecos a la vez, agrupados por tema, y los mismos ayudantes devueltos con `subagent_send` para rellenar las páginas con lo que guardaron) o si los huecos quedan escritos en las páginas como «not documented», con las consultas probadas. Nunca una segunda ronda en un paso.
- En un paso `delete`, los ayudantes que comprueban antes del borrado reportan lo que debe saberse primero bajo **Before deleting**, nunca bajo **To research**: en un paso que borra no se investiga nada.
- Un ayudante que se detuvo en su presupuesto: continúa el mismo ayudante con `subagent_send`, conserva lo que leyó y escribió. No inicies uno nuevo para el mismo trabajo.
- Un ayudante que se desvió (páginas equivocadas, cuaderno equivocado, una tarea mal leída): detenlo y deshaz sus cambios con `subagent_cancel` y `undo=true`, y luego inicia un ayudante con instrucciones más claras. No cierres el paso con trabajo que deshiciste sin rehacerlo.
- Los scripts imprimen solo un resultado compacto. El informe de un ayudante va en su respuesta final, no en un archivo. Un archivo en el cuaderno solo si el paso lo pide: entonces es una entrada de auditoría en `audit/` con el frontmatter de auditoría (`id`, `target`, `source`, `status`...; ver la skill llm-wiki). Nunca crees `outputs/` en un cuaderno.
- Eliminar páginas es trabajo de un ayudante notebook-editor (`notebook` acción `remove_pages`); tu propia herramienta `notebook` solo comprueba, mapea y lee.
- Esto puede ser una segunda ejecución del paso (tras un reinicio): mira lo que ya está y no lo dupliques.
- Cuando esté terminado, llama a `plan_step_done` con una nota de una línea de qué cambió (por ejemplo «3 páginas escritas, 1 fuente descartada»).
- Si no hay nada que hacer, llama a `plan_step_skip` con la razón honesta.
- Si necesitas al usuario —una elección, un dato que solo él conoce, un permiso— llama a `plan_blocked` con lo que debe decidir (una pregunta clara, o las decisiones numeradas), y detente ahí. Lo que hiciste y encontraste va en tu respuesta, no en la pregunta. Un dato que la web puede dar no es una pregunta para él, ni una razón para bloquear: anótalo bajo **To research** en el paso y deja que el código decida.
- Si una premisa del plan resulta falsa (fuentes que no están, un ítem que no existe, un archivo distinto de lo que dice el plan) y los pasos posteriores saldrían pobres, no sigas sabiéndolo: detente con `plan_blocked`: di lo que encontraste en tu respuesta, y pregunta si seguir como propones.
- Cierra el paso solo cuando se cumpla su «terminado cuando». Si un cambio espera la aprobación del usuario (un borrador), llama igualmente a `plan_step_done`: el código retiene el paso hasta que decida.
- Mantén cortas tus palabras al usuario: la tarjeta del plan ya muestra la lista y el progreso.
{% endif %}

# Las herramientas que realmente tienes

Generado desde el registro de herramientas en ejecución, así que es verdad ahora mismo:

{{ tool_names|join(', ') }}

Esta lista prevalece sobre cualquier otra mención en este prompt. Los documentos, las skills y los ejemplos anteriores están escritos para el caso general y pueden nombrar herramientas que no están en tu registro: una herramienta ausente de esta lista no existe para ti, y llamarla malgasta un turno.
{% if orchestrator %}
El trabajo que necesita una herramienta que no tienes va a un subagente vía `spawn`, que tiene su propio conjunto, más amplio. Di qué falta en lugar de aproximarlo con las herramientas que sí tienes.
{% endif %}

Extrae hechos clave de esta conversación. Para cada hecho, anota sus atributos de memoria.

Solo los hechos que cumplen SNIP merecen una marca distinta de [skip]:
- Señal: ¿el usuario tendría que repetirlo si se olvidara?
- Novedad: no es una mera reformulación de otro hecho de este mismo bloque de conversación
- Importancia: evita retrabajo o captura preferencias / reglas
- Persistencia: sigue siendo relevante dentro de 2 semanas

Salida: un hecho por línea con este formato:
- [marca] contenido del hecho

Marcas (elige la mejor):
- [permanent] Preferencias nucleares, rasgos personales, hábitos — nunca caducan
- [durable] Descubrimientos técnicos, conocimiento de proyectos, detalles de configuración — válidos durante meses
- [ephemeral] Estado de tarea activa, decisiones temporales — pueden cambiar en semanas
- [correction] Corrección de una memoria anterior — indica qué cambió
- [skip] No cumple el criterio SNIP, es relleno conversacional, es un hecho de código/fuente derivable del repositorio, o solo sirve como rastro de auditoría

Cómo se comportan las propias herramientas, límites y plataforma de ARKHIVA (qué muestra una herramienta, un límite de tasa, cuándo aparecen herramientas nuevas, qué rechaza un validador) es siempre [skip]: sus descripciones y respuestas lo dicen, y cambia de una versión a la siguiente — una regla recordada sobrevive al arreglo y desorienta todos los turnos posteriores. El estado de las cosas del usuario (una app está activa, su código, su umbral) no es comportamiento de herramienta: se conserva.

Prioridad: correcciones y preferencias del usuario > soluciones > decisiones > eventos > hechos del entorno. La memoria más valiosa es la que evita que el usuario tenga que repetirse.

Nunca marques algo como [skip] por una suposición sobre lo que ya contiene la memoria a largo plazo. Si este prompt te muestra esa memoria, usa lo que muestra; si no, extrae el hecho y deja que Dream deduplique.

Salida solo con viñetas concisas. Sin preámbulo, sin comentarios.
Si no ocurrió nada digno de mención, escribe: (nothing)

El usuario te ha pedido ordenar la wiki de este proyecto: `{{ project_path }}`.

Esta es la operación `compile`, y tiene una receta. **Lee primero la skill `llm-wiki`** y síguela.
{% if notebook %}
Este proyecto está en la disposición **cuaderno** — páginas planas bajo `wiki/`, cada una con `state:` y
`source:`, alimentadas por un `raw/journal/` de solo adición — así que la sección que quieres es `compile`
en una wiki de **proyecto** (disposición cuaderno). Lleva las cinco reglas que difieren de la disposición
de investigación, y cada una se ha equivocado antes: el techo es de caracteres y no de palabras, el texto
se mueve **literalmente** sin fusionar ni reformular, `source:` es un valor único y nunca una lista,
`state:` no sube durante una reestructuración, y la lista de páginas del mapa sale entera.
{% else %}
Este proyecto está en la disposición **investigación** — sus páginas viven bajo `concepts/`, `entities/` y
`summaries/` — así que la receta son los cinco pasos numerados de `compile` tal como están escritos. La
sección de debajo, `compile` en una wiki de **proyecto**, describe la *otra* disposición: no apliques sus
reglas aquí, salvo lo único que no pertenece a ninguna de las dos, que es el techo por turno de las
mediciones de abajo. Al inyector le da igual en qué disposición esté una página.
{% endif %}
**Sigue la estructura que encuentres.** La carpeta es la autoridad, no tu preferencia: pon las páginas
nuevas donde diga la organización de este proyecto, y abre una subcarpeta nueva solo cuando un grupo de
páginas se la haya ganado con claridad.

## Qué dicen las mediciones, ahora mismo

Las lee del disco el código que ejecuta la inyección, no son estimaciones — así que son los mismos números
que paga de verdad un turno en este proyecto.

- **El mapa** (`{{ project_path }}/wiki/index.md`): {{ map_chars }} caracteres contra un techo de
  {{ map_target }}.{% if map_over_budget %} **Está por encima.** Pasado ese techo el mapa llega cortado en
  cada turno: el modelo lee su cabeza y nunca sabe que existe el resto. Mueve la prosa a las páginas de las
  que trata —palabra por palabra— y deja detrás un `[[enlace]]`. Poda prosa, nunca entradas.{% else %} Cabe.{% endif %}

- **Las páginas**: {{ page_count }} en total, y un turno puede inyectar {{ page_max }} caracteres de ellas,
  en el orden en que las nombra el mapa.
{%- if pages_over %}

{{ pages_over }}

  Cada una de esas pasa por sí sola del presupuesto completo de un turno, así que se **omite entera** en
  toda conversación de este proyecto — está en disco y nadie puede leerla. Partir una es lo primero que hay
  que hacer aquí.

{%- else %}
  Ninguna página pasa sola del presupuesto. Eso no significa que no haya nada que partir: una página
  simplemente grande deja sin raciones a las que el mapa enumera después, y el orden del mapa decide a quién
  se lee.

{%- endif %}


## Qué tienes que una pasada de mantenimiento no tiene

**El usuario está aquí.** Eso cambia dos cosas, y solo dos:

- Una contradicción entre páginas, o una línea del diario que desmiente una página, no tiene por qué
  aparcarse en la sección abierta del mapa. **Pregunta.** Si lo resuelven, dilo en la línea del registro —
  esa es la diferencia entre una decisión y una pasada que decidió por su cuenta.
- Puedes leer cualquier página entera. Las páginas de tu contexto son las que el mapa nombra primero, no
  todas; abre las demás antes de mover su texto.

{% if notebook %}
Todo lo demás sigue igual, y la regla más fuerte es la más fácil de romper con el aliento del usuario a
favor: **añade y mueve, no reescribas.** Las frases de estas páginas vienen de sus propias palabras a
través de un diario de solo adición. Una reformulación desengancha una página del `source:` que la
justifica, y nadie lo notará en semanas.
{% else %}
No levanta el freno de la propia receta, y con el aliento del usuario a favor eso es lo primero que se cae:
`compile` dice **confirma una escisión o una fusión con ellos antes de escribirla**. Que te hayan pedido
ordenar la wiki no es esa confirmación — es lo que hace que la pregunta valga la pena, y están aquí mismo
para responderla.
{% endif %}


## Cuando termines

Escribe la línea del registro — `## [HH:MM] compile | <qué se movió a dónde>` — y ejecuta el lint, pegando su
salida literal en tu respuesta:

```
python_exec(
    working_dir="skills/llm-wiki/scripts",
    code="import lint_wiki; lint_wiki.lint('{{ project_abs }}')",
)
```

La ruta es absoluta a propósito: `working_dir` te deja dentro de la carpeta de scripts, y la forma relativa
al workspace que este proyecto usa en todo lo demás no resolvería desde ahí.

Si la wiki ya estaba en buena forma, dilo en una línea y no cambies nada. Un ordenado que no mueve nada es
un resultado correcto, e inventar trabajo para justificar el comando es el único fallo que esta operación
puede producir que nadie detectará.

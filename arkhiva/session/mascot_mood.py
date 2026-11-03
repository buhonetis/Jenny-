"""L'umore della mascotte, letto dagli emoji della risposta.

Dopo ogni turno WebUI ARKHIVA reagisce alla risposta che ha appena dato con una
faccia — felice, triste o arrabbiata — e la reazione diventa il frame
``mascot_mood`` che il client traduce in un'espressione. Da dove venga la
reazione e' tutto qui: dagli emoji che lei stessa ha scritto, attraverso un
dizionario. **Nessuna richiesta al modello**, quindi nessun costo e nessuna
dipendenza dal provider o dalla lingua.

Fino al 24/09/2026 la reazione la dava il modello, con una richiesta da tre
token dopo ogni turno. Su un modello che ragiona di default i tre token
finivano a pensare, il verdetto era sempre neutro e le facce non comparivano
mai — sul telefono, per settimane, senza che nessuno se ne accorgesse. Il
segnale che serviva c'era gia': ARKHIVA le emozioni le scrive.

Le regole che il codice tiene:

- **si legge solo la risposta**, l'ultima riga della assistente. Se l'ultima
  riga e' dell'utente il turno e' finito in errore, e l'errore ha gia' la sua
  faccia dal frame ``error``;
- **contano solo gli emoji suoi**: codice e citazioni si tolgono prima;
- **meglio nessuna faccia che quella sbagliata**: gli emoji ambigui e quelli
  che non sono emozioni restano fuori dal dizionario, e il neutro non manda
  frame;
- **vince la faccia con piu' voti, e a parita' l'ultima**: il tono di una
  risposta sta in coda.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from arkhiva.session.history_meta import is_synthetic_history_row
from arkhiva.utils.helpers import strip_think

if TYPE_CHECKING:
    from arkhiva.session.manager import Session

# Il vocabolario vive in un **dataset**, non nel codice: ``MOODS``, il neutro, la
# tabella emoji→umore e le faccine di testo stanno in
# ``arkhiva/templates/datasets/mascot_mood.json``. Aggiungere una faccia e'
# aggiungere una riga li'; cambiare qui una tabella sarebbe la seconda copia che
# diverge dalla prima.
#
# Sono le espressioni che **esistono disegnate**: l'arte comanda, non il
# vocabolario. Fino all'08/09/2026 erano cinque e comprendevano ``worried`` e
# ``surprised``, che non hanno una faccia; ``angry`` invece ce l'ha.
#
# Il criterio e' la faccia che si disegna, non la sfumatura: con tre espressioni
# «contenta», «sollevata», «complice» e «affettuosa» sono tutte ``happy``.
# Fuori dal dataset di proposito: gli ambigui (😅 🙃 😬 🤔 😐 😑 😶 👀 🤷 😳 😱
# 🫠 🥱 🤫 🧐 🤌) e tutto cio' che non e' un'emozione (☀️ 🌧️ 🍝 📅 🚗, bandiere,
# oggetti, frecce).
DATASET_PATH = "templates/datasets/mascot_mood.json"


@dataclass(frozen=True)
class _MoodDataset:
    """Il vocabolario, nella forma in cui il codice lo usa."""

    moods: tuple[str, ...]
    neutral: str
    emoji: Mapping[str, tuple[str, ...]]
    emoticons: tuple[tuple[str, str], ...]


@lru_cache(maxsize=1)
def _dataset() -> _MoodDataset:
    """Legge il dataset dal pacchetto. Assente o malformato e' un errore, non un vuoto.

    Un vocabolario vuoto non farebbe fallire niente: le facce semplicemente non
    comparirebbero piu', che e' esattamente il guasto silenzioso che questo
    modulo esiste per evitare.
    """
    import json
    import pkgutil

    raw = pkgutil.get_data("arkhiva", DATASET_PATH)
    if raw is None:
        raise RuntimeError(f"mascot mood dataset not found: {DATASET_PATH}")
    data = json.loads(raw.decode("utf-8"))
    moods = tuple(data["moods"])
    emoji = {mood: tuple(items) for mood, items in data["emoji"].items()}
    unknown = set(emoji) - set(moods)
    if unknown:
        raise RuntimeError(f"mascot mood dataset: moods not declared: {sorted(unknown)}")
    return _MoodDataset(
        moods=moods,
        neutral=str(data["neutral"]),
        emoji=emoji,
        emoticons=tuple((item["pattern"], item["mood"]) for item in data["emoticons"]),
    )


_DATASET = _dataset()
MOODS: tuple[str, ...] = _DATASET.moods
NEUTRAL_MOOD = _DATASET.neutral
MOOD_EMOJI: Mapping[str, tuple[str, ...]] = _DATASET.emoji
_EMOTICONS: tuple[tuple[str, str], ...] = _DATASET.emoticons
_EMOTICON_RE = re.compile(
    r"(?<![\w:;/>'])(" + "|".join(p for p, _ in _EMOTICONS) + r")(?!\w)"
)

# ``U+FE0F`` (presentazione emoji) e i cinque toni di pelle: un 👍🏽 e' un 👍.
_NORMALIZE_RE = re.compile("[\ufe0f\U0001F3FB-\U0001F3FF]")
# Blocchi di codice (anche non chiusi), codice in linea, righe citate.
_FENCE_RE = re.compile(r"```.*?(?:```|\Z)", re.S)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_QUOTE_RE = re.compile(r"^[ \t]*>.*$", re.M)


def _normalize(text: str) -> str:
    return _NORMALIZE_RE.sub("", text)


def _build_index(table: Mapping[str, tuple[str, ...]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for mood, emojis in table.items():
        for emoji in emojis:
            index[_normalize(emoji)] = mood
    return index


_EMOJI_TO_MOOD: dict[str, str] = _build_index(MOOD_EMOJI)
# Le sequenze ZWJ del dizionario (😮‍💨) sono lunghe piu' di un carattere: la
# ricerca prova prima la chiave piu' lunga.
_MAX_KEY_LEN = max(len(k) for k in _EMOJI_TO_MOOD)


@dataclass(frozen=True)
class MoodVerdict:
    """La faccia, e da cosa e' stata decisa (per il log: mai il testo)."""

    mood: str
    decided_by: str | None = None
    votes: int = 0


def _own_text(text: str) -> str:
    """La risposta senza cio' che non e' suo: codice e citazioni."""
    text = _FENCE_RE.sub(" ", text)
    text = _INLINE_CODE_RE.sub(" ", text)
    return _QUOTE_RE.sub(" ", text)


def _signals(text: str) -> list[tuple[int, str, str]]:
    """``(posizione, faccia, segno)`` per ogni emoji o faccina riconosciuta.

    Una sequenza ZWJ si cerca intera e, se non e' nel dizionario, per il suo
    primo emoji: ❤️‍🔥 vale ❤️, 😶‍🌫️ non vale niente perche' 😶 e' fuori.
    """
    found: list[tuple[int, str, str]] = []
    i = 0
    while i < len(text):
        for length in range(min(_MAX_KEY_LEN, len(text) - i), 0, -1):
            chunk = text[i:i + length]
            mood = _EMOJI_TO_MOOD.get(chunk)
            if mood:
                found.append((i, mood, chunk))
                i += length
                break
        else:
            i += 1
    for m in _EMOTICON_RE.finditer(text):
        token = m.group(1)
        mood = next(mood for pattern, mood in _EMOTICONS if re.fullmatch(pattern, token))
        found.append((m.start(), mood, token))
    found.sort(key=lambda s: s[0])
    return found


def mood_from_reply(text: str | None) -> MoodVerdict:
    """La faccia che la risposta porta, o ``neutral`` se non ne porta nessuna.

    Vince la faccia con piu' segni; a parita', quella il cui ultimo segno viene
    piu' tardi — «scusa il ritardo 😔 ma eccolo 🎉» e' una risposta contenta.
    """
    if not isinstance(text, str) or not text:
        return MoodVerdict(NEUTRAL_MOOD)
    signals = _signals(_normalize(_own_text(text)))
    if not signals:
        return MoodVerdict(NEUTRAL_MOOD)
    votes: dict[str, int] = {}
    last: dict[str, tuple[int, str]] = {}
    for position, mood, token in signals:
        votes[mood] = votes.get(mood, 0) + 1
        last[mood] = (position, token)
    top = max(votes.values())
    winner = max((m for m, v in votes.items() if v == top), key=lambda m: last[m][0])
    return MoodVerdict(winner, decided_by=last[winner][1], votes=top)


def _text_of(message: Mapping[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, str):
        return ""
    return strip_think(content).strip()


def _is_conversation_row(message: Mapping[str, Any]) -> bool:
    """Una riga scritta o letta dalla persona: niente comandi, niente sintetici.

    Un rientro di subagent o uno sprone a un goal non sono "l'utente ha detto".
    """
    if message.get("_command") is True:
        return False
    if is_synthetic_history_row(message):
        return False
    return message.get("role") in ("user", "assistant")


def last_reply(session: Session) -> str | None:
    """L'ultima risposta della assistente, o ``None`` se non c'e' niente da sentire.

    Si scorre dalla coda. La **prima** riga di conversazione deve essere della
    assistente: se e' dell'utente il turno e' finito in errore (o e' ancora
    aperto) e l'errore ha gia' la sua faccia, gratis, dal frame ``error``. Le
    righe strumentali (tool call, risultati) hanno contenuto non testuale e si
    saltano; una riga vuota pure.

    Nessun minimo di lunghezza: «ok 😊» e' un umore.
    """
    for message in reversed(session.messages):
        if not isinstance(message, Mapping) or not _is_conversation_row(message):
            continue
        text = _text_of(message)
        if not text:
            continue
        return text if message.get("role") == "assistant" else None
    return None

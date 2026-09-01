"""telegram — the studio's Telegram messaging seam.

One signed envelope to the hosted n8n fan-out workflow, and one catalogue of
message templates, so a Telegram message stops being composed by hand at every
call site.

The package is deliberately dependency-free (Python 3.9+ standard library only)
so it runs unchanged inside the /studio container, on a bare VPS, or under cron
on a laptop. That is not an aesthetic preference: there is no `pip` in the
container, and `studio-ops/bin/studio-cpu-watchdog` already hand-rolled its own
Python copy of the signing envelope because reaching a Node implementation was
not possible from where it ran.

Public surface:

    from telegram import Seam, Catalogue, Template, DeliveryVerifier, decode_update

Everything else is an implementation detail and may change.
"""

from .inbound import Answer, decode_update
from .keyboard import Button, decode, encode, keyboard
from .seam import Seam, SendResult
from .template import Catalogue, Message, Template
from .text import chunk, plain, tg_len
from .verify import DeliveryVerifier, Verdict

__version__ = "1.0.0"

__all__ = [
    "Answer",
    "Button",
    "Catalogue",
    "DeliveryVerifier",
    "Message",
    "Seam",
    "SendResult",
    "Template",
    "Verdict",
    "__version__",
    "chunk",
    "decode",
    "decode_update",
    "encode",
    "keyboard",
    "plain",
    "tg_len",
]

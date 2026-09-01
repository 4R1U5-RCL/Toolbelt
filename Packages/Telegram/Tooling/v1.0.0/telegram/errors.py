"""The error taxonomy.

The distinction that matters here is **caller-visible vs caller-fatal**. A
message that fails to send must never take down the thing that was trying to
report — a notification is by definition not the work. So `seam.send` catches
everything below and returns a result object instead of raising (the same
fail-soft discipline as `packages/notify/bin/notify.mjs`, which always exits 0).

The exceptions still exist, and are still classified, because the *offline*
surface — building a template, encoding a keyboard, validating a config — must
fail loudly and early. A `callback_data` that is one byte too long is not a
runtime hiccup to swallow; it is a message that will look fine and do nothing
when pressed (TG-03).
"""


class TelegramError(Exception):
    """Base class for every error this package raises deliberately."""


class ConfigError(TelegramError):
    """Credentials or settings are unusable. Always raised before any send."""


class TemplateError(TelegramError):
    """A template is malformed, unknown, or missing a field it declared required.

    Raised while *building* a message, never while delivering one.
    """


class KeyboardError(TelegramError):
    """A keyboard cannot be encoded safely.

    Overwhelmingly this means `callback_data` exceeded Telegram's 64-byte cap.
    Deliberately fatal rather than truncating: a truncated key still renders a
    perfectly normal-looking button that silently acts on the wrong row, or on
    nothing at all, and nobody finds out for weeks (TG-03, IN-30).
    """


class SendError(TelegramError):
    """A delivery attempt failed but may succeed later (timeout, 429, 5xx)."""


class FatalSendError(SendError):
    """The seam rejected the call and retrying cannot help.

    A bad signature, an unknown webhook path, a malformed body. Distinguished
    from `SendError` so a caller that does choose to retry does not spend an
    hour re-sending something the receiver will never accept (TG-05).
    """

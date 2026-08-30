"""Command-line entry point.

    scrape url https://example.com --format markdown
    scrape url https://example.com --chunk --max-tokens 800 --format json -o out.json
    scrape batch --input urls.txt --format json
    cat urls.txt | scrape batch --format markdown

Three subcommands (``url``, ``batch``, ``version``) dispatch through ``_COMMANDS``.
The real backend is assembled in ``_client`` — the one place a live credential
and ``HttpClient`` meet; tests monkeypatch that seam and pass a fake backend.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Callable, Dict, List, Optional

from . import __version__
from .client import build_client
from .config import Config, load_config
from .engine import Outcome, scrape_many, scrape_url
from .errors import ScrapeError
from .render import render_chunks, render_document

EXIT_OK = 0
EXIT_FATAL = 2

log = logging.getLogger("scrape")


# -- dependency assembly (the real seam; tests replace this) -----------------

def _client(config: Config):
    return build_client(config)


# -- commands ----------------------------------------------------------------

def cmd_url(args: argparse.Namespace) -> int:
    config = _config_from_args(args)
    client = _client(config)
    doc = scrape_url(args.url, client, config)
    out = render_chunks(doc, config.out_format) if config.chunk else render_document(doc, config.out_format)
    _write(out, args.out)
    return EXIT_OK


def cmd_batch(args: argparse.Namespace) -> int:
    urls = _read_urls(args.input)
    if not urls:
        log.error("no URLs given (pass --input FILE or pipe them on stdin)")
        return EXIT_FATAL
    config = _config_from_args(args)
    client = _client(config)
    outcomes = scrape_many(urls, client, config, on_error=args.on_error)
    _write(_render_batch(outcomes, config.out_format, config.chunk), args.out)
    failed = [o for o in outcomes if not o.ok]
    for o in failed:
        log.error("failed: %s — %s", o.url, o.error)
    log.info("scraped: %d ok, %d failed", len(outcomes) - len(failed), len(failed))
    return EXIT_FATAL if outcomes and len(failed) == len(outcomes) else EXIT_OK


def cmd_version(args: argparse.Namespace) -> int:
    print("scrape {0}".format(__version__))
    return EXIT_OK


_COMMANDS: Dict[str, Callable[[argparse.Namespace], int]] = {
    "url": cmd_url,
    "batch": cmd_batch,
    "version": cmd_version,
}


# -- wiring ------------------------------------------------------------------

def _config_from_args(args: argparse.Namespace) -> Config:
    ov: Dict[str, object] = {}
    for flag, key in (
        ("backend", "backend"),
        ("base_url", "base_url"),
        ("api_key_env", "api_key_env"),
        ("format", "out_format"),
        ("max_tokens", "max_tokens"),
        ("overlap", "overlap"),
        ("max_chars", "max_chars"),
        ("timeout", "timeout"),
        ("retries", "retries"),
    ):
        value = getattr(args, flag, None)
        if value is not None:
            ov[key] = value
    if getattr(args, "formats", None) is not None:
        ov["formats"] = [s.strip() for s in args.formats.split(",") if s.strip()]
    if getattr(args, "no_clean", None):
        ov["clean"] = False
    if getattr(args, "chunk", None):
        ov["chunk"] = True
    if getattr(args, "allow_insecure", None):
        ov["allow_insecure"] = True
    return load_config(getattr(args, "config", None), ov)


def _render_batch(outcomes: List[Outcome], fmt: str, chunked: bool) -> str:
    if fmt == "json":
        import json

        rows = []
        for o in outcomes:
            row: Dict[str, object] = {"url": o.url, "ok": o.ok}
            if o.document is not None:
                row["document"] = o.document.to_dict()
            if o.error is not None:
                row["error"] = o.error
            rows.append(row)
        return json.dumps(rows, indent=2, ensure_ascii=False)
    parts = []
    for o in outcomes:
        if o.document is None:
            continue
        parts.append(render_chunks(o.document, fmt) if chunked else render_document(o.document, fmt))
    return ("\n\n" + "=" * 72 + "\n\n").join(parts)


def _read_urls(source: Optional[str]) -> List[str]:
    if source in (None, "-"):
        text = sys.stdin.read()
    else:
        with open(source, "r", encoding="utf-8") as fh:
            text = fh.read()
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def _write(text: str, out: Optional[str]) -> None:
    if out and out != "-":
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
        log.info("wrote %s", out)
    else:
        print(text)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scrape", description="Scrape web pages into LLM-ready text via Firecrawl.")
    parser.add_argument("--version", action="version", version="scrape {0}".format(__version__))
    subs = parser.add_subparsers(dest="command")

    def with_common(sub: argparse.ArgumentParser) -> argparse.ArgumentParser:
        sub.add_argument("-c", "--config", help="JSON config file (flags override it)")
        sub.add_argument("-v", "--verbose", action="store_true", help="log status to stderr")
        sub.add_argument("-o", "--out", help="write to FILE instead of stdout")
        sub.add_argument("--format", choices=("markdown", "json", "text"), help="output format (default markdown)")
        sub.add_argument("--formats", help="Firecrawl formats to request, comma-separated (default markdown)")
        sub.add_argument("--no-clean", action="store_true", default=None, help="skip markdown normalization")
        sub.add_argument("--chunk", action="store_true", default=None, help="split into token-bounded chunks")
        sub.add_argument("--max-tokens", type=int, help="chunk size in ~tokens (default 1500)")
        sub.add_argument("--overlap", type=int, help="chunk overlap in ~tokens (default 0)")
        sub.add_argument("--max-chars", type=int, help="hard char cap on the markdown (default/cap 40000)")
        sub.add_argument("--backend", help="scrape backend (default firecrawl)")
        sub.add_argument("--base-url", help="backend base URL")
        sub.add_argument("--api-key-env", help="env var holding the API key (default FIRECRAWL_API_KEY)")
        sub.add_argument("--timeout", type=float, help="per-request timeout seconds (default 60)")
        sub.add_argument("--retries", type=int, help="transient-error retries (default 3)")
        sub.add_argument("--allow-insecure", action="store_true", default=None, help="permit http:// URLs")
        return sub

    p_url = with_common(subs.add_parser("url", help="scrape a single URL"))
    p_url.add_argument("url", help="the URL to scrape")

    p_batch = with_common(subs.add_parser("batch", help="scrape many URLs (one per line)"))
    p_batch.add_argument("-i", "--input", help="file of URLs, or - for stdin (default stdin)")
    p_batch.add_argument("--on-error", choices=("continue", "stop"), default="continue", help="batch failure policy")

    subs.add_parser("version", help="print the version")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_FATAL
    logging.basicConfig(
        level=logging.INFO if getattr(args, "verbose", False) else logging.WARNING,
        format="%(message)s",
    )
    try:
        return _COMMANDS[args.command](args)
    except ScrapeError as err:
        log.error("scrape failed: %s", err)
        return EXIT_FATAL
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return EXIT_OK

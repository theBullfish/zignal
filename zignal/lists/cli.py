"""CLI entry point: scan Temple + Z13, emit all surfaces."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from .walker import scan_local, scan_remote_z13
from .emit import emit_all, _payload

TEMPLE_ROOTS = [
    "/mnt/work",
    "/home/watchdog",
]
Z13_ROOTS = [
    "/home/z13",
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="zignal-lists")
    ap.add_argument("--temple-roots", nargs="*", default=TEMPLE_ROOTS)
    ap.add_argument("--z13-roots", nargs="*", default=Z13_ROOTS)
    ap.add_argument("--no-z13", action="store_true",
                    help="Skip remote Z13 scan (Temple-only).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print summary; do not write outputs.")
    args = ap.parse_args(argv)

    items = scan_local([Path(p) for p in args.temple_roots], host="temple")
    if not args.no_z13:
        items.extend(scan_remote_z13(args.z13_roots))

    summary = _payload(items)
    print(f"[lists] {summary['count']} open items, "
          f"oldest {summary['oldest_age_days']} days")

    if args.dry_run:
        for it in summary["items"][:10]:
            print(f"  {it['age_days']:3}d  {it['status']:<8}  "
                  f"{it['item_id']:<10}  {it['host']}:{it['source_path']}:{it['line']}")
        return 0

    result = emit_all(items)
    print(f"[lists] json={result['json_path']} "
          f"z13_pushed={result['z13_memory_pushed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

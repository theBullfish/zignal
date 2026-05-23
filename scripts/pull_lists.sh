#!/usr/bin/env bash
# Z13-side: pull lists.json from Temple, re-render UNFINISHED_LISTS.md.
# Closes L1.07's push-not-pull gap. Run at session start (or wire
# into a session-start hook) so the markdown reflects the *current*
# state of the Temple scanner, not the last-pushed copy.
exec python3 -m zignal.lists.pull "$@"

#!/usr/bin/env python3
"""
signal_notation.py — Signal-Chain Context Format for Zignal
============================================================

Replaces AAAK with a signal-chain-aware notation designed for:
  - .zdx module compatibility
  - Modulation-weighted emotions (not flat labels)
  - Confidence scoring on every extraction
  - Trust weight propagation
  - Any LLM reads it natively — no decoder required

FORMAT:
  Header:   SIG|FILE_NUM|ENTITY|DATE|TITLE|TRUST_FLOOR
  Node:     N:ID|ENTITIES|topics|"key_quote"|WEIGHT|CONFIDENCE
  Signal:   S:emotion[weight]--mod-->emotion[weight]
  Link:     L:ID<->ID|label|coherence
  State:    ST:domain_vector|[wing:weight, wing:weight, ...]
  Flag:     F:ID|FLAG_TYPE

SIGNAL MODULATIONS (not flat emotions — transitions with weights):
  Each emotion is a node in a signal chain with a weight [0.01-0.99].
  Modulations describe how one state transforms into another:
    --resonate-->   amplifies
    --modulate-->   transforms
    --dampen-->     reduces
    --invert-->     flips
    --cascade-->    triggers chain reaction

FLAGS:
  ORIGIN    = origin moment (birth of something)
  CORE      = core belief or identity pillar
  SENSITIVE = handle with absolute care
  PIVOT     = signal-chain direction change
  GENESIS   = led directly to something existing
  DECISION  = explicit decision or choice
  TECHNICAL = technical architecture or implementation
  UNCERTAIN = low confidence extraction
  CONFLICT  = contradicts existing knowledge
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# === SIGNAL STATES (richer than emotion codes) ===

SIGNAL_STATES = {
    # Core states
    "vulnerability": "vul", "vulnerable": "vul",
    "joy": "joy", "joyful": "joy",
    "fear": "fear", "afraid": "fear",
    "trust": "tru", "trusting": "tru",
    "grief": "grf", "grieving": "grf",
    "wonder": "wnd", "awe": "wnd",
    "rage": "rag", "anger": "rag",
    "love": "lov", "devotion": "lov",
    "hope": "hop", "hopeful": "hop",
    "despair": "dsp", "hopelessness": "dsp",
    "peace": "pce", "calm": "pce",
    "relief": "rlf",
    "humor": "hmr", "dark_humor": "hmr",
    "tenderness": "tnd",
    "raw_honesty": "raw", "brutal_honesty": "raw",
    "self_doubt": "dbt", "doubt": "dbt",
    "anxiety": "anx", "anxious": "anx",
    "exhaustion": "exh", "burned_out": "exh",
    "conviction": "cnv", "certain": "cnv",
    "passion": "psn", "quiet_passion": "psn",
    # Signal-chain specific states
    "flow": "flw",          # hyperfocus lock-in
    "scatter": "sct",        # attention fragmentation
    "resonance": "rsn",      # cross-domain pattern match
    "dissonance": "dsn",     # conflicting signals
    "clarity": "clr",        # signal resolved
    "noise": "nse",          # unresolved interference
    "momentum": "mtm",       # building toward something
    "stall": "stl",          # forward motion blocked
}

MODULATION_TYPES = {
    "resonate": "amplifies signal",
    "modulate": "transforms signal",
    "dampen": "reduces signal",
    "invert": "flips signal",
    "cascade": "triggers chain reaction",
}

FLAG_TYPES = {
    "ORIGIN", "CORE", "SENSITIVE", "PIVOT", "GENESIS",
    "DECISION", "TECHNICAL", "UNCERTAIN", "CONFLICT",
}


class SignalNode:
    """A single extracted context node with confidence scoring."""

    def __init__(
        self,
        node_id: int,
        entities: List[str],
        topics: List[str],
        key_quote: str = "",
        weight: float = 0.5,
        confidence: float = 0.5,
        flags: List[str] = None,
        wing_vector: Dict[str, float] = None,
    ):
        self.node_id = node_id
        self.entities = entities
        self.topics = topics
        self.key_quote = key_quote
        self.weight = max(0.01, min(0.99, weight))
        self.confidence = max(0.01, min(0.99, confidence))
        self.flags = [f for f in (flags or []) if f in FLAG_TYPES]
        self.wing_vector = wing_vector or {}

    def render(self) -> str:
        parts = [f"N:{self.node_id}"]
        parts.append("|".join(self.entities) if self.entities else "_")
        parts.append(",".join(self.topics) if self.topics else "_")
        if self.key_quote:
            # Truncate for compactness
            q = self.key_quote[:120].replace('"', "'").replace("\n", " ")
            parts.append(f'"{q}"')
        else:
            parts.append('""')
        parts.append(f"W{self.weight:.2f}")
        parts.append(f"C{self.confidence:.2f}")
        return "|".join(parts)


class SignalChain:
    """A modulation chain between signal states."""

    def __init__(self, transitions: List[Tuple[str, float, str, str, float]]):
        """
        transitions: list of (state_from, weight_from, modulation_type, state_to, weight_to)
        """
        self.transitions = transitions

    def render(self) -> str:
        if not self.transitions:
            return ""
        parts = []
        for i, (s_from, w_from, mod, s_to, w_to) in enumerate(self.transitions):
            code_from = SIGNAL_STATES.get(s_from, s_from[:3])
            code_to = SIGNAL_STATES.get(s_to, s_to[:3])
            if i == 0:
                parts.append(f"S:{code_from}[{w_from:.2f}]")
            parts.append(f"--{mod}-->{code_to}[{w_to:.2f}]")
        return "".join(parts)


class SignalDocument:
    """A complete signal notation document."""

    def __init__(
        self,
        file_num: int = 0,
        primary_entity: str = "",
        date: str = "",
        title: str = "",
        trust_floor: float = 0.5,
    ):
        self.file_num = file_num
        self.primary_entity = primary_entity
        self.date = date
        self.title = title
        self.trust_floor = max(0.01, min(0.99, trust_floor))
        self.nodes: List[SignalNode] = []
        self.chains: List[SignalChain] = []
        self.links: List[Tuple[int, int, str, float]] = []  # (id_a, id_b, label, coherence)
        self.state_vector: Dict[str, float] = {}  # wing weights

    def add_node(self, **kwargs) -> SignalNode:
        node = SignalNode(node_id=len(self.nodes), **kwargs)
        self.nodes.append(node)
        return node

    def add_chain(self, transitions: List[Tuple[str, float, str, str, float]]) -> SignalChain:
        chain = SignalChain(transitions)
        self.chains.append(chain)
        return chain

    def add_link(self, id_a: int, id_b: int, label: str, coherence: float = 0.5):
        coherence = max(0.01, min(0.99, coherence))
        self.links.append((id_a, id_b, label, coherence))

    def set_state(self, wing_vector: Dict[str, float]):
        """Set the fuzzy wing vector for this document."""
        self.state_vector = {k: max(0.01, min(0.99, v)) for k, v in wing_vector.items()}

    def render(self) -> str:
        """Render complete signal notation document."""
        lines = []

        # Header
        lines.append(
            f"SIG|{self.file_num}|{self.primary_entity}|{self.date}|{self.title}|TF{self.trust_floor:.2f}"
        )

        # State vector (fuzzy wings)
        if self.state_vector:
            pairs = ",".join(f"{k}:{v:.2f}" for k, v in sorted(self.state_vector.items()))
            lines.append(f"ST|[{pairs}]")

        # Nodes
        for node in self.nodes:
            lines.append(node.render())
            for flag in node.flags:
                lines.append(f"F:{node.node_id}|{flag}")

        # Signal chains
        for chain in self.chains:
            rendered = chain.render()
            if rendered:
                lines.append(rendered)

        # Links
        for id_a, id_b, label, coherence in self.links:
            lines.append(f"L:{id_a}<->{id_b}|{label}|COH{coherence:.2f}")

        return "\n".join(lines)

    def token_estimate(self) -> int:
        return len(self.render()) // 4


# === Extraction helpers ===

def extract_signal_states(text: str) -> List[Tuple[str, float]]:
    """
    Extract signal states from text with estimated weights.
    Returns list of (state_name, weight).
    """
    text_lower = text.lower()
    found = []
    for full_name, code in SIGNAL_STATES.items():
        if full_name in text_lower:
            # Weight based on frequency and position
            count = text_lower.count(full_name)
            position = text_lower.index(full_name) / max(len(text_lower), 1)
            # Earlier = higher weight, more mentions = higher weight
            weight = min(0.99, 0.3 + (count * 0.15) + ((1 - position) * 0.2))
            found.append((full_name, round(weight, 2)))
    return found


def detect_modulations(states: List[Tuple[str, float]]) -> List[Tuple[str, float, str, str, float]]:
    """
    Given a sequence of detected states, infer modulation types between them.
    """
    if len(states) < 2:
        return []

    transitions = []
    for i in range(len(states) - 1):
        s_from, w_from = states[i]
        s_to, w_to = states[i + 1]

        # Infer modulation type from weight change
        delta = w_to - w_from
        if delta > 0.2:
            mod = "resonate"
        elif delta < -0.2:
            mod = "dampen"
        elif (s_from in ("fear", "grief", "despair") and s_to in ("hope", "joy", "peace")):
            mod = "invert"
        elif abs(delta) < 0.1:
            mod = "modulate"
        else:
            mod = "cascade"

        transitions.append((s_from, w_from, mod, s_to, w_to))

    return transitions


def text_to_signal(
    text: str,
    file_num: int = 0,
    primary_entity: str = "",
    date: str = "",
    title: str = "",
    wing_vector: Dict[str, float] = None,
    trust_floor: float = 0.5,
) -> SignalDocument:
    """
    Convert raw text to signal notation document.

    This is a basic extraction — semantic clustering and LLM-assisted
    extraction should be layered on top for production use.
    """
    doc = SignalDocument(
        file_num=file_num,
        primary_entity=primary_entity,
        date=date,
        title=title,
        trust_floor=trust_floor,
    )

    if wing_vector:
        doc.set_state(wing_vector)

    # Split into paragraphs as basic chunking
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for i, para in enumerate(paragraphs[:20]):  # cap at 20 nodes per doc
        # Extract entities (capitalized words as rough heuristic)
        entities = list(set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', para)))[:5]

        # Extract topics (lowercase significant words)
        words = re.findall(r'\b[a-z]{4,}\b', para.lower())
        # Simple frequency-based topic extraction
        word_freq = {}
        for w in words:
            if w not in ("this", "that", "with", "from", "have", "been", "were", "they", "their", "about", "would", "could", "should", "there", "these", "those"):
                word_freq[w] = word_freq.get(w, 0) + 1
        topics = sorted(word_freq, key=word_freq.get, reverse=True)[:5]

        # Key quote: first sentence
        sentences = re.split(r'[.!?]+', para)
        key_quote = sentences[0].strip() if sentences else ""

        # Weight: longer paragraphs with more entities = more important
        weight = min(0.99, 0.3 + len(entities) * 0.1 + min(len(para) / 1000, 0.3))

        # Confidence: basic heuristic — more structure = higher confidence
        confidence = min(0.99, 0.4 + len(entities) * 0.08 + len(topics) * 0.05)

        # Flags
        flags = []
        para_lower = para.lower()
        if any(w in para_lower for w in ("decided", "decision", "chose", "choosing")):
            flags.append("DECISION")
        if any(w in para_lower for w in ("first time", "origin", "began", "started")):
            flags.append("ORIGIN")
        if any(w in para_lower for w in ("architecture", "implementation", "algorithm", "protocol")):
            flags.append("TECHNICAL")
        if any(w in para_lower for w in ("believe", "core", "fundamental", "always")):
            flags.append("CORE")

        doc.add_node(
            entities=entities,
            topics=topics,
            key_quote=key_quote,
            weight=weight,
            confidence=confidence,
            flags=flags,
            wing_vector=wing_vector,
        )

    # Extract signal chains
    states = extract_signal_states(text)
    if len(states) >= 2:
        transitions = detect_modulations(states)
        if transitions:
            doc.add_chain(transitions)

    # Link sequential nodes with coherence based on shared entities/topics
    for i in range(len(doc.nodes) - 1):
        n_a = doc.nodes[i]
        n_b = doc.nodes[i + 1]
        shared_entities = set(n_a.entities) & set(n_b.entities)
        shared_topics = set(n_a.topics) & set(n_b.topics)
        coherence = min(0.99, 0.3 + len(shared_entities) * 0.15 + len(shared_topics) * 0.1)
        if coherence > 0.35:
            doc.add_link(i, i + 1, "sequential", coherence)

    return doc


# === CLI ===

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python signal_notation.py <file>")
        print("  Converts a text file to signal notation")
        sys.exit(0)

    filepath = sys.argv[1]
    with open(filepath, "r") as f:
        text = f.read()

    doc = text_to_signal(
        text,
        file_num=0,
        primary_entity=Path(filepath).stem,
        title=Path(filepath).stem,
    )
    print(doc.render())
    print(f"\n--- {doc.token_estimate()} estimated tokens ---")

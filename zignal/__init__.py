"""Zignal — Signal memory system. CFA topology, signal-chain cognition, trust-weighted retrieval."""

from .cli import main
from .version import __version__
from .signal_notation import SignalDocument, SignalNode, SignalChain, text_to_signal
from .knowledge_graph import KnowledgeGraph
from .layers import MemoryStack

__all__ = [
    "main", "__version__",
    "SignalDocument", "SignalNode", "SignalChain", "text_to_signal",
    "KnowledgeGraph", "MemoryStack",
]

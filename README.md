# LTID Replication Package

## Installation

External requirements needed to compute log graphs from java source: `JDK17`, `Maven`, `SrcML libraries`.

Python version requirement: `python ^= 3.13`.

`pip install ./ltid-toolkit`

## Quick Start

```python
from ltid.toolkit.log_graph import LogGraph
from prefixspan import make_trie
from np.typing import ArrayLike

# Compute log graph from java source code:
graph_a = LogGraph.from_source("/path/to/java/source/files")

# Alternatively, from a series of sequences of log event IDs:
logs: list[list[int]] = ...
graph_b = LogGraph.from_logs(logs)
```

## Project Structure

```sh
ltid_replication_package
├── README.md
├── ltid-log-graph (Java source log graph generator implementation)
├── ltid-toolkit (Toolkit/main package)
├── requirements.txt (Dependencies for scripts/experiments)
└── *.py (Scripts/experiments)
```

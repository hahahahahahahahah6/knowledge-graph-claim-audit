# Documentation claim auditor

Version 0.1.0. An offline Python source and documentation auditor. It compares exact prose phrases with static call patterns for the checked capability. Source is parsed, never executed. No network access, telemetry, or file writes occur during an audit.

## Install and use

Requires Python 3.9 or newer.

```sh
pip install knowledge-graph-claim-audit
knowledge-graph-claim-audit --version
knowledge-graph-claim-audit audit . --json
python3 -m knowledge_graph_claim_audit audit . --verbose --ignore vendor --ignore build --fail-on medium
```

The default directory is the current directory. Exit status is 0 when no finding meets the threshold, 2 when one does, and 1 for usage or I/O errors. The default threshold is high; medium also includes test-only evidence. JSON contains a verdict, findings with id, severity and message, evidence paths, and file counts. Repeat the single-value ignore option to exclude path prefixes.

Root README.md and Markdown files under a docs component are checked. Fenced blocks are excluded; inline code counts. Paragraphs are normalized separately: lowercase, expanded contractions, replaced hyphens, collapsed whitespace. Exact boundary matches prefer longer phrases, then alphabetical order; denial spans are removed first.

Python files are scanned recursively without following symlinks. The fixtures, docs, and examples components are excluded from evidence. Test paths count separately. Invalid syntax contributes no evidence. Pairs must occur in one module, imports are resolved through aliases, and local definitions shadow route names. A positive statement without source still produces a high finding; a denial without source passes.

```text
documented-knowledge-graph-claim-false HIGH
 documented-knowledge-graph-claim-false MEDIUM (test-only evidence)
documented-no-knowledge-graph-claim-false HIGH
```

## Differentiation

The adjacent auditors cover distinct operations:

```text
semantic-search-claim-audit: retrieval alone, no graph store.
named-entity-recognition-claim-audit: entity spans alone, no relations, no graph.
retrieval-augmented-generation-claim-audit: retrieve-then-generate, no graph construction, no triple store, no SPARQL/Cypher.
document-question-answering-claim-audit: pipeline instance call with no graph.
```

## Honest limitations

The following matching hazards are reproduced from the design requirements:

```text
- The bare word "sparql" is deliberately a
  KNOWLEDGEGRAPH phrase: in Python project docs it almost always
  names graph querying. A doc that mentions SPARQL in an unrelated
  sense is a false positive; the same accepted shape as other
  families' short phrases.
- "relationship extraction", "triple extraction", and "extracts
  triples" are deliberately phrases: they can also describe pure
  NLP extraction with no graph store. The tool flags the claim;
  only the code decides.
- "graph database" and "graph databases" are deliberately phrases:
  they can describe a storage backend choice rather than a
  built graph of entities and relations. A doc that says so while
  its code never constructs a graph or runs a graph query is
  exactly the false claim this family catches.
- "entities and relationships" and "entity graph" are deliberately
  phrases: they can describe a data-model diagram or a schema
  description with no graph operation in code.
- "node and edge" is deliberately a phrase: it can describe counts
  or a diagram legend, not a built graph.
- A networkx graph construction plus an add-node / add-edge call
  cannot distinguish a knowledge graph from any other graph (a
  dependency graph, a call graph): the pair is the graph
  fingerprint, and the doc claim plus the code's graph operation
  together decide. A plain graph tool whose docs never claim a
  knowledge graph passes untouched.
- An rdflib `Graph` that only ever loads and dumps data with no
  add / parse / query call on it is NOT counted: constructing a
  container is not operating on a graph, per the family rule that
  the construction must be paired with an operation call.
- A neo4j driver that is only constructed and never runs a query is
  NOT counted: opening a connection is not querying a graph.
- A hand-rolled triple store that adds triples with
  differently-named methods (for example `store.put(subject,
  predicate, object)`) is NOT detected: the generic route covers
  only the listed method names. The tool covers the rdflib /
  networkx / neo4j / LangChain routes plus the listed generic
  names only.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each pair must sit in a single
  module.

```

## Development

```sh
python3 -m unittest discover
python3 -m build
```

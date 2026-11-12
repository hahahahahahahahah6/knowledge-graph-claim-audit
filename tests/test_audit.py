import unittest
import ast
from pathlib import Path
from knowledge_graph_claim_audit import phrases

class PhraseOracle(unittest.TestCase):
    def test_exact_vocabulary(self):
        expected = {'KNOWLEDGEGRAPH': ('knowledge graph', 'knowledge graphs', 'knowledge graph model', 'knowledge graph models', 'knowledge graph based', 'knowledge graph powered', 'knowledge graph database', 'knowledge graph databases', 'knowledge graph extraction', 'knowledge graph construction', 'knowledge graph query', 'knowledge graph queries', 'knowledge graph querying', 'builds a knowledge graph', 'builds knowledge graphs', 'build knowledge graph', 'builds knowledge graph', 'creates a knowledge graph', 'creates knowledge graphs', 'extracts a knowledge graph', 'entity relationship graph', 'entity relation graph', 'entity graph', 'knowledge base graph', 'graph of entities', 'graph of entities and relationships', 'graph of entities and relations', 'entities and relationships', 'entity and relationship extraction', 'relationship extraction', 'triple extraction', 'extracts triples', 'stores triples', 'triple store', 'triple stores', 'rdf graph', 'rdf graphs', 'rdf triple', 'rdf triples', 'sparql', 'sparql query', 'sparql queries', 'sparql endpoint', 'cypher query', 'cypher queries', 'graph database', 'graph databases', 'property graph', 'property graphs', 'node and edge'), 'NOKNOWLEDGEGRAPH': ('no knowledge graph', 'does not build a knowledge graph', 'without a knowledge graph', 'no knowledge graphs', 'does not support knowledge graphs', 'knowledge graph not supported', 'does not use a knowledge graph', 'no graph database', 'does not use a graph database', 'no triple store', 'does not store triples', 'no sparql', 'does not support sparql', 'no cypher', 'does not use cypher', 'no rdf', 'does not use rdf', 'relational only', 'relational database only', 'no entity graph', 'does not extract triples', 'no relationship extraction', 'does not build knowledge graphs', 'flat data only'), 'GENERIC_NAMES': ('build_knowledge_graph', 'create_knowledge_graph', 'query_knowledge_graph', 'add_to_knowledge_graph', 'extract_knowledge_graph', 'construct_knowledge_graph', 'kg_query', 'query_kg', 'build_kg', 'create_kg', 'add_triple', 'add_triples', 'add_relation', 'add_relationship', 'add_entity', 'extract_triples', 'extract_relations', 'link_entities', 'graph_query', 'kg_add', 'kg_build', 'knowledge_graph_query', 'add_knowledge_triple', 'build_entity_graph'), 'RDFLIB_NAMES': ('Graph',), 'RDFLIB_OPERATIONS': ('add', 'parse', 'query'), 'NETWORKX_NAMES': ('Graph', 'DiGraph', 'MultiGraph', 'MultiDiGraph'), 'NETWORKX_OPERATIONS': ('add_node', 'add_nodes_from', 'add_edge', 'add_edges_from'), 'NEO4J_NAMES': ('GraphDatabase.driver',), 'NEO4J_SESSION': ('session',), 'NEO4J_OPERATIONS': ('run', 'execute_query', 'execute_write', 'execute_read'), 'LANGCHAIN_NAMES': ('LLMGraphTransformer', 'Neo4jGraph', 'GraphCypherQAChain'), 'TRANSFORMER_OPERATIONS': ('convert_to_graph_documents',), 'LANGCHAIN_GRAPH_OPERATIONS': ('query', 'add_graph_documents'), 'CHAIN_OPERATIONS': ('invoke', 'run', 'ainvoke', 'arun')}
        tree = ast.parse(Path(phrases.__file__).read_text())
        actual = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)}
        self.assertEqual(actual, expected)
        for values in expected.values():
            self.assertEqual(len(values), len(set(values)))

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from knowledge_graph_claim_audit.audit import audit, evidence, claims
from knowledge_graph_claim_audit.__main__ import main

GOOD = {'rdf_add': 'import rdflib\ng = rdflib.Graph()\ng.add(t)', 'rdf_parse': 'import rdflib\nrdflib.Graph().parse(p)', 'rdf_query': 'import rdflib\ng=rdflib.Graph()\ng.query(q)', 'rdf_from': 'from rdflib import Graph as G\nG().add(t)', 'nx_edge': 'import networkx as nx\ng=nx.DiGraph()\ng.add_edge(a,b)', 'nx_node': 'import networkx as nx\ng=nx.Graph()\ng.add_node(a)', 'nx_from': 'from networkx import DiGraph as D\ng=D()\ng.add_edges_from(e)', 'nx_chain': 'import networkx as nx\nnx.DiGraph().add_edge(a,b)', 'neo_run': 'from neo4j import GraphDatabase\nGraphDatabase.driver(uri).session().run(q)', 'neo_execute': 'from neo4j import GraphDatabase as GD\nd=GD.driver(uri)\ns=d.session()\ns.execute_query(q)', 'neo_write': 'from neo4j import GraphDatabase\nGraphDatabase.driver(uri).session().execute_write(f)', 'neo_with': 'from neo4j import GraphDatabase\ndriver = GraphDatabase.driver(uri)\nwith driver.session() as s:\n    s.run(q)', 'langchain_invoke': 'from langchain.chains import GraphCypherQAChain\nc=GraphCypherQAChain()\nc.invoke(q)', 'lc_factory': 'from langchain.chains import GraphCypherQAChain as C\nC.from_llm(llm).invoke(q)', 'lc_transform': 'from langchain_experimental import LLMGraphTransformer\nt=LLMGraphTransformer(llm)\nt.convert_to_graph_documents(docs)', 'lc_chain': 'from langchain import LLMGraphTransformer\nLLMGraphTransformer(llm).convert_to_graph_documents(docs)', 'lc_query': 'from langchain import Neo4jGraph\ng=Neo4jGraph()\ng.query(q)', 'lc_add': 'from langchain import Neo4jGraph\ng=Neo4jGraph()\ng.add_graph_documents(d)', 'generic_query': 'x.query_kg(q)', 'generic_build': 'x.build_knowledge_graph(d)', 'generic_add': 'x.add_triple(t)', 'generic_extract': 'x.extract_triples(d)', 'generic_from': 'from custom import build_kg as go\ngo(d)'}
BAD = {'imports': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain', 'rdf_lone': 'import rdflib\ng=rdflib.Graph()', 'nx_lone': 'import networkx as nx\nnx.Graph()', 'driver_lone': 'from neo4j import GraphDatabase\nGraphDatabase.driver(uri)', 'session_lone': 'from neo4j import GraphDatabase\nGraphDatabase.driver(uri).session()', 'neo_with_no_run': 'from neo4j import GraphDatabase\ndriver = GraphDatabase.driver(uri)\nwith driver.session() as s:\n    pass', 'transform_lone': 'import langchain\nLLMGraphTransformer(llm)', 'chain_lone': 'import langchain\nGraphCypherQAChain()', 'factory_lone': 'import langchain\nGraphCypherQAChain.from_llm(llm)', 'entity': 'nlp(text).ents', 'relations': 'nlp.extract(text)', 'retrieval': 'db.similarity_search(q)', 'generation': 'llm.generate(q)', 'answering': 'from transformers import pipeline\np=pipeline("question-answering")\np(q)', 'training': 'trainer.train()', 'subprocess': 'import subprocess\nsubprocess.run(["graph", "query"])', 'bare_generic': 'build_kg(d)', 'reference': 'x.query_kg', 'string': 's="x.query_kg(q)"', 'syntax': 'x.query_kg(', 'shadow_generic': 'def query_kg(): pass\nx.query_kg(q)', 'shadow_method': 'class X:\n def add_triple(self): pass\nx.add_triple(t)', 'shadow_rdf': 'from rdflib import Graph\nclass Graph: pass\nGraph().add(t)', 'shadow_alias': 'from rdflib import Graph as G\ndef G(): pass\nG().add(t)', 'unbound_add': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.add(q)', 'wrong_add': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.add(q)', 'unbound_parse': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.parse(q)', 'wrong_parse': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.parse(q)', 'unbound_query': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.query(q)', 'wrong_query': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.query(q)', 'unbound_add_node': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.add_node(q)', 'wrong_add_node': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.add_node(q)', 'unbound_add_edge': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.add_edge(q)', 'wrong_add_edge': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.add_edge(q)', 'unbound_run': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.run(q)', 'wrong_run': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.run(q)', 'unbound_convert_to_graph_documents': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.convert_to_graph_documents(q)', 'wrong_convert_to_graph_documents': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.convert_to_graph_documents(q)', 'unbound_invoke': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx.invoke(q)', 'wrong_invoke': 'import rdflib\nimport networkx\nimport neo4j\nimport langchain\nx=Other()\nx.invoke(q)'}

class EvidenceTests(unittest.TestCase):
    pass


def make_route_test(source, expected):
    def test(self):
        self.assertEqual(evidence(source), expected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'README.md').write_text('Uses a knowledge graph.')
            (root / 'app.py').write_text(source)
            result = audit(root)
            self.assertEqual(result['verdict'], 'PASS' if expected else 'FAIL')
    return test


for _name, _source in GOOD.items():
    setattr(EvidenceTests, 'test_good_' + _name, make_route_test(_source, True))
for _name, _source in BAD.items():
    setattr(EvidenceTests, 'test_bad_' + _name, make_route_test(_source, False))


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def cli(self, *args):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                code = main(['audit', str(self.root)] + list(args))
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), errors.getvalue()

    def test_bad_exact(self):
        self.put('README.md', 'knowledge graph')
        self.put('app.py', 'pass')
        code, output, _ = self.cli()
        self.assertEqual(code, 2)
        self.assertIn('documented-knowledge-graph-claim-false HIGH', output)

    def test_good(self):
        self.put('README.md', 'knowledge graph')
        self.put('app.py', GOOD['langchain_invoke'])
        self.assertEqual(self.cli()[0], 0)

    def test_test_only(self):
        self.put('README.md', 'knowledge graph')
        self.put('tests/helper.py', GOOD['generic_query'])
        self.assertEqual(self.cli()[0], 0)
        self.assertIn('MEDIUM', self.cli()[1])
        self.assertEqual(self.cli('--fail-on', 'medium')[0], 2)

    def test_denial(self):
        self.put('README.md', 'no knowledge graph')
        self.put('app.py', GOOD['generic_query'])
        code, output, _ = self.cli()
        self.assertEqual(code, 2)
        self.assertIn('documented-no-knowledge-graph-claim-false HIGH', output)
        self.assertEqual(len(audit(self.root)['findings']), 1)

    def test_no_claim(self):
        self.put('README.md', 'A useful tool.')
        self.put('app.py', GOOD['generic_query'])
        self.assertEqual(self.cli()[0], 0)

    def test_no_source_asymmetry(self):
        self.put('README.md', 'knowledge graph')
        self.assertEqual(self.cli()[0], 2)
        self.put('README.md', 'no knowledge graph')
        self.assertEqual(self.cli()[0], 0)

    def test_fences(self):
        for marker in ('```', '~~~', '   ````', '  ~~~~'):
            with self.subTest(marker=marker):
                self.put('README.md', marker + 'text\nrag\n' + marker + '\nSafe.')
                self.assertEqual(self.cli()[0], 0)

    def test_inline(self):
        self.put('README.md', 'Supports `knowledge graph`.')
        self.assertEqual(self.cli()[0], 2)

    def test_normalization(self):
        self.assertEqual(claims("Doesn't build a knowledge-graph"), ([], ['does not build a knowledge graph']))
        self.assertEqual(claims('knowledge graphical'), ([], []))
        self.assertEqual(claims('knowledge graph models')[0], ['knowledge graph models'])
        self.assertEqual(claims('knowledge\n\ngraph')[0], [])

    def test_all_phrases(self):
        for phrase in phrases.KNOWLEDGEGRAPH:
            with self.subTest(phrase=phrase):
                self.assertEqual(claims(phrase), ([phrase], []))
        for phrase in phrases.NOKNOWLEDGEGRAPH:
            with self.subTest(phrase=phrase):
                self.assertEqual(claims(phrase), ([], [phrase]))

    def test_docs_selection(self):
        self.put('other.md', 'knowledge graph')
        self.assertEqual(self.cli()[0], 0)
        self.put('nested/docs/details.md', 'knowledge graph')
        self.assertEqual(self.cli()[0], 2)

    def test_split_modules(self):
        for first, second in [
            ('import rdflib\ng=rdflib.Graph()', 'g.add(t)'),
            ('import networkx as nx\ng=nx.Graph()', 'g.add_edge(a,b)'),
            ('from neo4j import GraphDatabase\ns=GraphDatabase.driver(u).session()', 's.run(q)'),
            ('import langchain\nc=GraphCypherQAChain()', 'c.invoke(q)'),
        ]:
            with self.subTest(first=first):
                self.put('README.md', 'knowledge graph')
                self.put('a.py', first)
                self.put('b.py', second)
                self.assertEqual(self.cli()[0], 2)

    def test_excluded_components(self):
        self.put('README.md', 'knowledge graph')
        for component in ('fixtures', 'examples', 'docs'):
            self.put(component + '/app.py', GOOD['generic_query'])
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(audit(self.root)['test_evidence'], [])

    def test_test_filename_patterns(self):
        self.put('README.md', 'knowledge graph')
        for filename in ('test_feature.py', 'feature_test.py', 'tests/util.py'):
            self.put(filename, GOOD['generic_query'])
        self.assertEqual(len(audit(self.root)['test_evidence']), 3)
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.cli('--fail-on', 'medium')[0], 2)

    def test_symlinks(self):
        self.put('README.md', 'knowledge graph')
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside)
            (target / 'app.py').write_text(GOOD['generic_query'])
            (self.root / 'app.py').symlink_to(target / 'app.py')
            (self.root / 'linked').symlink_to(target, target_is_directory=True)
            self.assertEqual(self.cli()[0], 2)
            self.assertEqual(audit(self.root)['source_files'], 0)

    def test_ignore(self):
        self.put('docs/one.md', 'knowledge graph')
        self.put('extra/docs/two.md', 'knowledge graph')
        self.assertEqual(self.cli('--ignore', 'docs', '--ignore', 'extra')[0], 0)

    def test_json(self):
        self.put('README.md', 'knowledge graph')
        code, output, _ = self.cli('--json')
        self.assertEqual(code, 2)
        data = json.loads(output)
        self.assertEqual(data['verdict'], 'FAIL')
        self.assertTrue(data['findings'][0]['message'])

    def test_verbose(self):
        self.assertIn('source_files', self.cli('--verbose')[1])

    def test_usage(self):
        self.assertEqual(self.cli('--fail-on', 'HIGH')[0], 1)
        self.assertEqual(self.cli('--unknown')[0], 1)
        self.assertEqual(self.cli('--ignore', 'one', 'two')[0], 1)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main([])
        self.assertEqual(raised.exception.code, 1)

    def test_bad_path(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', str(self.root / 'missing')]), 1)

    def test_version_and_module(self):
        result = subprocess.run([sys.executable, '-m', 'knowledge_graph_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '0.1.0')
        result = subprocess.run([sys.executable, '-m', 'knowledge_graph_claim_audit', 'audit', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_all_generic_attributes(self):
        for name in phrases.GENERIC_NAMES:
            self.assertTrue(evidence('x.' + name + '(q)'))

    def test_all_route_attributes(self):
        for lib, constructor, operations in [
            ('rdflib','Graph',phrases.RDFLIB_OPERATIONS),
            *[('networkx', n, phrases.NETWORKX_OPERATIONS) for n in phrases.NETWORKX_NAMES],
            ('neo4j','GraphDatabase.driver(u).session',phrases.NEO4J_OPERATIONS),
            ('langchain','LLMGraphTransformer',phrases.TRANSFORMER_OPERATIONS),
            ('langchain','Neo4jGraph',phrases.LANGCHAIN_GRAPH_OPERATIONS),
            ('langchain','GraphCypherQAChain',phrases.CHAIN_OPERATIONS)]:
            for op in operations:
                self.assertTrue(evidence('import '+lib+'\n'+constructor+'().'+op+'(q)'))

class AdditionalEvidenceTests(unittest.TestCase):
    def test_module_aliases(self):
        for source in (
            'import rdflib as r; r.Graph().add(t)',
            'import networkx as n; n.MultiDiGraph().add_nodes_from(t)',
            'import neo4j as n; n.GraphDatabase.driver(u).session().execute_read(f)',
            'import langchain.chains as lc; lc.GraphCypherQAChain.from_llm(llm).arun(q)',
            'from custom import query_kg; query_kg(q)',
        ):
            with self.subTest(source=source):
                self.assertTrue(evidence(source))

    def test_import_gates(self):
        for source in ('Graph().add(t)', 'DiGraph().add_edge(a,b)',
                       'GraphDatabase.driver(u).session().run(q)',
                       'LLMGraphTransformer().convert_to_graph_documents(d)',
                       'Neo4jGraph().query(q)', 'GraphCypherQAChain().invoke(q)'):
            self.assertFalse(evidence(source))

    def test_shadowed_routes(self):
        for source in (
            'from neo4j import GraphDatabase\nclass GraphDatabase: pass\nGraphDatabase.driver(u).session().run(q)',
            'from langchain import Neo4jGraph\ndef Neo4jGraph(): pass\nNeo4jGraph().query(q)',
            'from networkx import DiGraph as D\nclass D: pass\nD().add_edge(a,b)',
            'from langchain import GraphCypherQAChain as C\nclass C: pass\nC.from_llm().invoke(q)',
            'from custom import build_kg as go\ndef go(): pass\ngo(q)',
            'import rdflib\nclass X:\n def add(self): pass\nrdflib.Graph().add(t)',
        ):
            self.assertFalse(evidence(source))

    def test_bare_imported_reference(self):
        self.assertFalse(evidence('from custom import build_kg; build_kg'))

    def test_binding_alias_and_cycle(self):
        self.assertTrue(evidence('import rdflib; a=rdflib.Graph(); b=a; b.add(t)'))
        self.assertFalse(evidence('import rdflib; a=b; b=a; a.add(t)'))

    def test_no_operation_rdf(self):
        self.assertFalse(evidence('import rdflib; g=rdflib.Graph(); g.serialize()'))

    def test_readme_has_no_claims(self):
        readme = Path(__file__).resolve().parents[1] / 'README.md'
        self.assertEqual(claims(readme.read_text()), ([], []))

if __name__ == '__main__':
    unittest.main()

# Lab 16: Knowledge Graph + LLM

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Knowledge graphs provide structured, verifiable knowledge that complements LLMs' statistical knowledge. This lab covers entity/relation extraction, graph construction, Neo4j/Cypher, GraphRAG architecture, SPARQL, ontology design, and KG-augmented generation patterns.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Knowledge Graph + LLM Architecture              │
├──────────────────────────────────────────────────────────────┤
│  TEXT CORPUS → NLP Pipeline                                  │
│  ├── NER: Entity extraction (Person, Org, Location, Event)   │
│  ├── RE: Relation extraction (works_at, located_in)          │
│  └── Coreference resolution (he/she/it → entity)            │
├──────────────────────────────────────────────────────────────┤
│  KNOWLEDGE GRAPH (Neo4j / RDF Store)                         │
│  Nodes: entities | Edges: relations | Properties: attributes │
├──────────────────────────────────────────────────────────────┤
│  QUERY: Natural language → Cypher/SPARQL → Graph results     │
│         ↓ retrieved subgraph                                  │
│  LLM → structured answer with citations                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Why Knowledge Graphs for LLMs?

**LLM Limitations KGs Solve:**
```
LLMs have:
  ✗ Hallucinations (confident wrong facts)
  ✗ Knowledge cutoff (training data date)
  ✗ Can't reason about specific relationships reliably
  ✗ No guaranteed citation to source

Knowledge Graphs provide:
  ✓ Verified facts with provenance
  ✓ Up-to-date (can be updated without retraining)
  ✓ Multi-hop reasoning (A → B → C)
  ✓ Structured queries (no hallucination in retrieval)
```

**KG vs Vector DB for RAG:**

| Dimension | Vector DB RAG | Knowledge Graph RAG |
|-----------|--------------|---------------------|
| Query type | Semantic similarity | Structured + semantic |
| Reasoning | Single-hop | Multi-hop |
| Facts | Fuzzy | Precise |
| Relations | Implicit | Explicit |
| Updates | Re-embed document | Add/update triples |
| Use case | General knowledge retrieval | Complex relation queries |

---

## Step 2: Entity and Relation Extraction

**Named Entity Recognition (NER) Categories:**

| Category | Examples | NLP Labels |
|----------|---------|-----------|
| Person | Elon Musk, Sam Altman | PERSON |
| Organization | OpenAI, Google DeepMind | ORG |
| Location | San Francisco, EU | GPE/LOC |
| Product | GPT-4, Gemini, Claude | PRODUCT |
| Event | AlphaGo match, IPO | EVENT |
| Date/Time | Q1 2024, March 15 | DATE/TIME |

**Relation Extraction Types:**
```
(Person, works_at, Organization)
(Organization, acquired, Organization)
(Person, invented, Technology)
(Organization, headquartered_in, Location)
(Product, competes_with, Product)
(Technology, is_a, Category)
```

**Extraction Pipeline:**
```
Raw text
  ↓ 1. Coreference resolution: "He founded OpenAI" → "Sam Altman founded OpenAI"
  ↓ 2. NER: identify entity spans
  ↓ 3. Entity linking: "Apple" → Apple Inc (not fruit)
  ↓ 4. Relation extraction: (Subject, Predicate, Object) triples
  ↓ 5. Deduplication + merging
  ↓ 6. KG ingestion
```

---

## Step 3: Neo4j and Cypher Query Language

**Neo4j Graph Model:**
```
Nodes: entities with labels and properties
Edges: relationships with types and properties

Example:
(:Person {name: "Sam Altman"}) -[:CEO_OF]-> (:Organization {name: "OpenAI"})
(:Organization {name: "OpenAI"}) -[:CREATED]-> (:Product {name: "GPT-4"})
(:Product {name: "GPT-4"}) -[:COMPETES_WITH]-> (:Product {name: "Claude"})
```

**Cypher Query Examples:**
```cypher
-- Find all products created by a person's organization
MATCH (p:Person)-[:CEO_OF]->(org:Organization)-[:CREATED]->(prod:Product)
WHERE p.name = "Sam Altman"
RETURN org.name, prod.name

-- Find 2-hop connections (shared competitors)
MATCH (a:Product)-[:COMPETES_WITH]-(shared)-[:COMPETES_WITH]-(b:Product)
WHERE a.name = "GPT-4" AND b.name <> "GPT-4"
RETURN DISTINCT b.name

-- Find shortest path
MATCH path = shortestPath(
  (a:Person {name: "Sam Altman"})-[*]-(b:Person {name: "Jeff Dean"})
)
RETURN path
```

**Cypher for LLM Context:**
```
User query: "What AI products compete with GPT-4?"

Text2Cypher (LLM): 
  MATCH (p:Product {name: 'GPT-4'})-[:COMPETES_WITH]-(competitor:Product)
  RETURN competitor.name, competitor.developer
  
Results: [Claude (Anthropic), Gemini (Google), Llama (Meta), ...]

LLM generates: "GPT-4 faces competition from Claude by Anthropic,
                Gemini by Google, and open-source Llama from Meta."
```

---

## Step 4: SPARQL Basics

SPARQL (SPARQL Protocol and RDF Query Language) is the standard for RDF knowledge graphs.

**RDF Triple Format:**
```
Subject → Predicate → Object
<OpenAI> → <rdf:type> → <Organization>
<GPT-4> → <dbo:developer> → <OpenAI>
<OpenAI> → <dbo:foundingYear> → "2015"
```

**SPARQL SELECT:**
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?model ?developer ?year
WHERE {
  ?model rdf:type dbo:ArtificialIntelligence .
  ?model dbo:developer ?developer .
  ?developer rdfs:label "OpenAI" .
  ?model dbo:releaseYear ?year .
}
ORDER BY DESC(?year)
LIMIT 10
```

**Ontology Design (OWL):**
```
Classes: ArtificialIntelligence, LargeLanguageModel, Organization
Subclasses: LargeLanguageModel rdfs:subClassOf ArtificialIntelligence
Properties: hasCapability, trainedOn, serves
Constraints: LargeLanguageModel hasCapability min 1 Capability
```

---

## Step 5: GraphRAG (Microsoft)

GraphRAG enhances RAG with community-level knowledge from graphs.

**GraphRAG vs Naive RAG:**
```
Naive RAG:
  Query → vector search → 5 chunks → LLM → answer
  Problem: misses connections across documents

GraphRAG:
  Documents → entity extraction → community detection → summaries
  Query → identify relevant communities → retrieve subgraph → LLM → answer
  Advantage: handles "what are the main themes?" type queries
```

**GraphRAG Pipeline:**
```
1. Text corpus → LLM-based entity/relation extraction
2. Build entity graph (deduplicated)
3. Community detection (Leiden algorithm)
4. Generate community summaries (LLM)
5. Index: vector + graph
6. Query:
   a. Global: search community summaries (high-level)
   b. Local: vector + graph retrieval (specific)
```

**Cost Note:**
```
GraphRAG is expensive: LLM calls to extract from every document
For 1M token corpus at GPT-4 prices: ~$50-200 for indexing
But: dramatically better at multi-document analysis queries
```

---

## Step 6: KG-Augmented Generation Patterns

**Pattern 1: KG as Fact-Checker:**
```
LLM generates response → extract claimed facts → verify against KG
If fact contradicts KG → flag as potential hallucination
If fact not in KG → mark as unverified
```

**Pattern 2: KG as Context Source:**
```
User query → entity recognition → KG subgraph retrieval
Subgraph → linearized to text → added to LLM context
LLM → responds grounded in verified KG facts
```

**Pattern 3: Text2Cypher:**
```
Natural language → LLM → Cypher/SPARQL query → execute against KG
Results → LLM → natural language answer
Advantages: precise, structured retrieval; no vector approximation
```

**Pattern 4: Hybrid KG + Vector:**
```
Query → KG structured search (for known entities) + Vector search (for semantics)
Merge results → LLM context → response

Best for: queries with both entity-specific and semantic components
```

---

## Step 7: Enterprise KG Use Cases

**Financial Services:**
```
Entity graph: companies, executives, subsidiaries, products, events
Relationships: owns, competes_with, regulated_by, invested_in

Use case: "What companies does our client have conflicts of interest with?"
KG query: (client) -[invested_in]-> (company) -[competes_with]-> (client_company)
```

**Cybersecurity Threat Intelligence:**
```
Entity graph: threat actors, malware, CVEs, industries, TTPs
Relationships: uses, targets, exploits, mitigated_by

Use case: "What attacks should we prioritize patching for?"
KG query: (APT29) -[uses]-> (malware) -[exploits]-> (CVE-YYYY-XXXX)
          WHERE CVE-YYYY-XXXX affects our infrastructure
```

**HR and Organizational:**
```
Entity graph: employees, skills, projects, departments, locations
Relationships: reports_to, has_skill, works_on, located_in

Use case: "Find me a team for this project who have Python + ML skills"
KG query: (project)-[:REQUIRES]->(skill:Python,ML) <- (employee)
```

---

## Step 8: Capstone — Threat Intel KG Traversal

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
from collections import defaultdict, deque

class KnowledgeGraph:
    def __init__(self):
        self.edges = defaultdict(list)
        self.nodes = set()
        self.edge_types = {}
    
    def add_triple(self, subject, predicate, obj):
        self.edges[subject].append((predicate, obj))
        self.edges[obj].append((f'inverse_{predicate}', subject))
        self.nodes.update([subject, obj])
        self.edge_types[(subject, obj)] = predicate
    
    def bfs(self, start, max_depth=3):
        visited = {start}
        queue = deque([(start, 0, [start])])
        paths = []
        while queue:
            node, depth, path = queue.popleft()
            if depth > 0:
                paths.append(path)
            if depth >= max_depth:
                continue
            for pred, neighbor in self.edges[node]:
                if neighbor not in visited and not pred.startswith('inverse'):
                    visited.add(neighbor)
                    queue.append((neighbor, depth+1, path+[f'-[{pred}]->', neighbor]))
        return paths
    
    def find_path(self, start, end, max_depth=4):
        queue = deque([(start, [start])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            if node == end:
                return path
            if len(path) >= max_depth:
                continue
            for pred, neighbor in self.edges[node]:
                if neighbor not in visited and not pred.startswith('inverse'):
                    visited.add(neighbor)
                    queue.append((neighbor, path+[f'-[{pred}]->', neighbor]))
        return None

kg = KnowledgeGraph()
triples = [
    ('APT29', 'uses', 'Spear_Phishing'),
    ('APT29', 'targets', 'Government_Sector'),
    ('APT29', 'uses', 'COZY_BEAR_Malware'),
    ('Spear_Phishing', 'exploits', 'Email_Vulnerability'),
    ('COZY_BEAR_Malware', 'uses', 'C2_Infrastructure'),
    ('C2_Infrastructure', 'hosted_on', 'Cloud_Provider'),
    ('Email_Vulnerability', 'mitigated_by', 'Email_Filtering'),
    ('Government_Sector', 'uses', 'Security_Operations_Center'),
    ('Security_Operations_Center', 'monitors', 'Network_Traffic'),
]
for s, p, o in triples:
    kg.add_triple(s, p, o)

print('=== Knowledge Graph: Enterprise Threat Intel ===')
print(f'Nodes: {len(kg.nodes)} | Edges: {len(triples)}')
print()
print('BFS from APT29 (depth=2):')
paths = kg.bfs('APT29', max_depth=2)
for path in paths[:5]:
    print(f'  {\" \".join(path)}')

print()
print('Path: APT29 -> Email_Filtering:')
path = kg.find_path('APT29', 'Email_Filtering')
if path:
    print(f'  {\" \".join(path)}')
else:
    print('  Path requires depth > 4, tracing manually:')
    print('  APT29 -[uses]-> Spear_Phishing -[exploits]-> Email_Vulnerability -[mitigated_by]-> Email_Filtering')

print()
print('SPARQL-style query (KG-augmented LLM context):')
print('  SELECT ?malware ?infrastructure WHERE {')
print('    ?threat uses ?malware .')
print('    ?malware uses ?infrastructure .')
print('    FILTER(?infrastructure = C2_Infrastructure)')
print('  }')
print('  Results: APT29 -> COZY_BEAR_Malware -> C2_Infrastructure')
"
```

📸 **Verified Output:**
```
=== Knowledge Graph: Enterprise Threat Intel ===
Nodes: 10 | Edges: 9

BFS from APT29 (depth=2):
  APT29 -[uses]-> Spear_Phishing
  APT29 -[targets]-> Government_Sector
  APT29 -[uses]-> COZY_BEAR_Malware
  APT29 -[uses]-> Spear_Phishing -[exploits]-> Email_Vulnerability
  APT29 -[targets]-> Government_Sector -[uses]-> Security_Operations_Center

Path: APT29 -> Email_Filtering:
  Path requires depth > 4, tracing manually:
  APT29 -[uses]-> Spear_Phishing -[exploits]-> Email_Vulnerability -[mitigated_by]-> Email_Filtering

SPARQL-style query (KG-augmented LLM context):
  SELECT ?malware ?infrastructure WHERE {
    ?threat uses ?malware .
    ?malware uses ?infrastructure .
    FILTER(?infrastructure = C2_Infrastructure)
  }
  Results: APT29 -> COZY_BEAR_Malware -> C2_Infrastructure
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| KG vs Vector DB | KG: structured, multi-hop, precise; Vector: semantic, fuzzy, single-hop |
| Entity Extraction | NER → Entity linking → Coreference resolution |
| Neo4j/Cypher | Graph database; pattern-matching queries; MATCH-WHERE-RETURN |
| SPARQL | Standard for RDF graphs; SELECT-WHERE with triple patterns |
| GraphRAG | Community detection + summaries; better for cross-document analysis |
| KG-Augmented Gen | Patterns: fact-checker, context source, Text2Cypher, hybrid |
| Use Cases | Threat intel, financial relationships, HR skills mapping |

**Next Lab:** [Lab 17: Real-Time AI Inference →](lab-17-real-time-ai-inference.md)

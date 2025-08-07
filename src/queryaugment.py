"""Collection of functions to enrich query results with additional data."""

from functools import partial
from rdflib import Graph, Namespace, URIRef, Literal


def URIRefs_from_results(result_set):
    uri_set = set()
    for tup in result_set:
        for value in tup:
            if isinstance(value, URIRef):
                uri_set.add(value)
    return uri_set

def value_in_set(value, testset):
    return value in testset

def augment_sparql_to_graph(source_graph, sparql_query, 
                          get_types=True, 
                          get_labels=True, 
                          get_literals=True, 
                          get_cross_links=True, 
                          sparql_option=False):
    """Augment SPARQL query results with additional data from the source graph."""
    # Execute the SPARQL query
    query_results = source_graph.query(sparql_query)
    
    # Augment the results with additional data
    entity_data = augment_query_results(source_graph, query_results, get_types, get_labels, get_literals, get_cross_links, sparql_option)
    new_g = Graph()
    for t in entity_data:
        new_g.add(t)
    return new_g


def augment_query_results(source_graph, 
                          query_results, 
                          get_types=True, 
                          get_labels=True, 
                          get_literals=True, 
                          get_cross_links=True, 
                          sparql_option=False):
    """Augment query results with additional data from the source graph."""
    entity_data = set()
    active_uris=URIRefs_from_results(query_results)
    inscope_uris_f = partial(value_in_set, testset=active_uris)
    for uri in active_uris:
        if get_types:
            entity_data=entity_data.union(set(get_type_triples(source_graph, uri, sparql_option=False)))
        if get_labels:
            entity_data=entity_data.union(set(get_label_triples(source_graph, uri, sparql_option=False)))
        if get_literals:
            entity_data=entity_data.union(set(get_literal_triples(source_graph, uri, sparql_option=False)))
        if get_cross_links:
            object_filter=list(filter(lambda x : inscope_uris_f(x[2]), get_object_triples(source_graph, uri, sparql_option=False)))
            test_loops = [(s,p,o) for s,p,o in object_filter if s==o]
            if len(test_loops) > 0:
                print(f"Warning: self-loop detected ")
                print(test_loops)
                assert False
            entity_data=entity_data.union(set(object_filter))
    return entity_data

def return_nodes_of_type(graph, type_set):
    node_set = set()
    for s,p,o in graph.triples((None, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), None)):
        if o in type_set:
            node_set.add(s)
    return node_set


def filter_triples_from_graph(graph, node_filter_set, predicate_filter_set, type_filter_set):
    new_g = Graph()

    # select nodes from type_filter set
    typed_exclusion_nodes = return_nodes_of_type(graph, type_filter_set)

    #print(typed_exclusion_nodes)

    node_filter_set = node_filter_set.union(typed_exclusion_nodes)
    
    for s,p,o in graph.triples((None, None, None)):
        if p not in predicate_filter_set and s not in node_filter_set and o not in node_filter_set:
            new_g.add((s,p,o))
    return new_g

def get_type_triples(graph, subject, sparql_option=True):
    """Given an RDF graph and a subject, return all type triples for that subject."""
    type_triples = []
    if sparql_option:
        sparql_query = """
                    SELECT ?subject ?isa ?type WHERE {
                        ?subject ?isa ?type .
                        VALUES ?isa {rdf:type} .
                    }
                    """
        type_triples = graph.query(sparql_query, initBindings={'subject': subject})
    else:
        # Fallback to direct graph traversal if SPARQL is not used
        for s, p, o in graph.triples((subject, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), None)):
            type_triples.append((s, p, o))
    return type_triples

def get_used_predicate_set(rdfgraph, sparql_method=True):
    #Compile a list of all the predicates *used* in the graph
    pset = set()
    if sparql_method:
        results = rdfgraph.query("""SELECT DISTINCT ?p { ?s ?p ?o}""")
        pset=set([r[0] for r in results])
    else:
        for s,p,o in rdfgraph.triples((None, None, None)):
            pset.add(p)
    return pset

def get_used_types_set(rdfgraph, sparql_method=True):
    #Compile a list of all the types assigned to entities in the graph
    tset = set()
    if sparql_method:
        results = rdfgraph.query("""SELECT DISTINCT ?type WHERE {
                        ?subject ?isa ?type .
                        VALUES ?isa {rdf:type} .
                    }""")
        tset=set([r[0] for r in results])
    else:
        for s, p, o in rdfgraph.triples((None, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), None)):
            tset.add(o)

    return tset

def get_used_entities_set(rdfgraph, sparql_method=True):
    #Compile a list of all the entities present in the graph
    eset = set()
    if sparql_method:
        results = rdfgraph.query("""SELECT DISTINCT ?entity 
                    
                    {
                        {SELECT DISTINCT ?entity WHERE {
                            ?entity ?p ?o .
                            FILTER( ISIRI(?entity) ).
                        }
                    }     
                    UNION
                        {SELECT DISTINCT ?entity WHERE {
                        ?s ?p ?entity .
                        FILTER( ISIRI(?entity) ).
                    }
                    }
                    }

                                 """)
        eset=set([r[0] for r in results])
    else:
        for s, p, o in rdfgraph.triples((None, None, None)):
            if isinstance(s, URIRef):
                eset.add(s)
            if isinstance(o, URIRef):
                eset.add(o)
    return eset

def get_label_triples(graph, subject, sparql_option=True):
    """Given an RDF graph and a subject, return all literal triples for that subject."""
    label_triples = []
    if sparql_option:
        sparql_query = """
                    SELECT ?subject ?predicate ?literal WHERE {
                        ?subject ?predicate ?literal .
                        FILTER(isLiteral(?literal)) .
                        { SELECT ?predicate WHERE { ?subtype rdfs:subPropertyOf* rdfs:label . }
                    }
                    """
        label_triples=graph.query(sparql_query, initBindings={'subject': subject})
    else:
        # Fallback to direct graph traversal if SPARQL is not used

        label_types = [l[0] for l in graph.query("""
            SELECT ?subtype WHERE {
                ?subtype rdfs:subPropertyOf* rdfs:label .
            }
        """)]
        for ltype in label_types:
            for s, p, o in graph.triples((subject, ltype, None)):
                if isinstance(o, Literal):
                    label_triples.append((s, p, o))
    return label_triples

def get_literal_triples(graph, subject, sparql_option=True):
    """Given an RDF graph and a subject, return all literal triples for that subject."""
    literal_triples = []
    if sparql_option:
        sparql_query = """
                    SELECT ?subject ?predicate ?literal WHERE {
                        ?subject ?predicate ?literal .
                        FILTER(isLiteral(?literal))
                    }
                    """
        literal_triples=graph.query(sparql_query, initBindings={'subject': subject})
    else:
        # Fallback to direct graph traversal if SPARQL is not used
        for s, p, o in graph.triples((subject, None, None)):
            if isinstance(o, Literal):
                literal_triples.append((s, p, o))
    return literal_triples

def get_object_triples(graph, subject, sparql_option=True):
    """Given an RDF graph and a subject, return all object triples for that subject."""
    object_triples = []
    if sparql_option:
        sparql_query = """
                    SELECT ?subject ?predicate ?object WHERE {
                        ?subject ?predicate ?object .
                        FILTER(isURI(?object))
                    }
                    """
        object_triples=graph.query(sparql_query, initBindings={'subject': subject})
    else:
        # Fallback to direct graph traversal if SPARQL is not used
        for s, p, o in graph.triples((subject, None, None)):
            if not isinstance(o, Literal): #watch out for bnodes
                object_triples.append((s, p, o))

    return object_triples


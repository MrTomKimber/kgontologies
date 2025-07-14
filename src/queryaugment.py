"""Collection of functions to enrich query results with additional data."""

from rdflib import Namespace, URIRef, Literal

def augment_query_results(query_results, additional_data):
    pass

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


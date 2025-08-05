# A collection of functions to provide UI ability to filter out unwanted graph content.

from rdflib import Graph, Namespace, URIRef, Literal
import src.queryaugment as queryaugment


def gen_predicate_filter_template(rdfgraph, sparql_method=True):
    predicates = queryaugment.get_used_predicate_set(rdfgraph, sparql_method=sparql_method)
    p_filt_d = dict()
    for p in predicates:
        p_filt_d[p]=True
    return p_filt_d

def gen_types_filter_template(rdfgraph, sparql_method=True):
    types = queryaugment.get_used_types_set(rdfgraph, sparql_method=sparql_method)
    t_filt_d = dict()
    for t in types:
        t_filt_d[t]=True
    return t_filt_d

def gen_entities_filter_template(rdfgraph, sparql_method=True):
    entities = queryaugment.get_used_entities_set(rdfgraph, sparql_method=sparql_method)
    e_filt_d = dict()
    for e in entities:
        e_filt_d[e]=True
    return dict(sorted([(k,v) for k,v in e_filt_d.items()], key=lambda x : x[0]))
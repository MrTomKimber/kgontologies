from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, SH
import uuid
import numpy as np


def rdflib_graph_from_dataframe(dataframe, data_namespace="http://data#"):

    DATA = Namespace(data_namespace)
    g = Graph(bind_namespaces="rdflib")
    g.bind("data", DATA)
    g.add ((DATA.row, RDF.type, OWL.Class))
    g.add ((DATA.row, RDFS.label, Literal("Row")))

    for c in dataframe.columns:
        g.add(( DATA[f"column({c})"], RDF.type, OWL.DatatypeProperty )) # Define the column as a datatype property
        g.add(( DATA[f"column({c})"], RDFS.label, Literal(c) )) # Attach a simple label to the datatype property
        g.add((DATA.row, DATA.has_field, DATA[f"column({c})"]))

    for row_i,data in dataframe.replace(np.nan, None).iterrows():
        row_url = DATA[uuid.uuid4().hex]
        row_index = Literal(row_i)
        g.add((row_url, RDF.type, DATA.row))
        g.add((row_url, DATA.row_ident, row_index))
        for c in dataframe.columns:
            p_url = DATA[f"column({c})"]
            if data[c] is not None:
                o_literal = Literal(data[c])
                g.add((row_url, p_url, o_literal))
    return g



def capture_entity_data(rdflib_graph, entity):
    """For a provided rdflib graph and an identified entity, extract
    all types, labels, literals and participating properties"""
    entity_types=None
    entity_labels=None
    entity_literals=dict()
    outbound_entity_properties=dict()
    inbound_entity_properties=dict()

    for s,p,o in rdflib_graph.triples((entity, RDF.type, None)):
        if entity_types is not None:
            entity_types.add(o)
        else:
            entity_types=set([o])

    for s,p,o in rdflib_graph.triples((entity, RDFS.label, None)):
        if entity_labels is not None:
            entity_labels.add(o)
        else:
            entity_labels=set([o])

    for s,p,o in rdflib_graph.triples((entity, None, None)):
        if isinstance(o, Literal):
            if p not in entity_literals:
                entity_literals[p]=set([o])
            else:
                entity_literals[p].add(o)
        else:
            if p in outbound_entity_properties:
                outbound_entity_properties[p].add(o)
            else:
                outbound_entity_properties[p]=set([o])
    for s,p,o in rdflib_graph.triples((None, None, entity)):
        if p in inbound_entity_properties:
            inbound_entity_properties[p].add(s)
        else:
            inbound_entity_properties[p]=set([s])
            
    return { "node" : entity, 
            "types" : entity_types, 
            "labels" : entity_labels, 
            "literals" : entity_literals, 
            "outbound_links" : outbound_entity_properties, 
            "inbound_links" : inbound_entity_properties }

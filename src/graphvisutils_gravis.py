"""A collection of generic graph visualisation utilities 
   intended to work with gravis and the gravis JSON Graph Format gJGF"""
# https://robert-haas.github.io/gravis-docs/rst/format_specification.html
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, SH
import networkx as nx
import uuid
from itertools import cycle
import src.colourschemes as colourschemes
import numpy as np
import pandas as pd

import src.graphloader as graphloader


def construct_property_table(entity_data):
    rows=[]
    panel_html_template="""
    <h2>Node: {title}</h2>
    <p>Type: {etype} </br>
    <p>Label: {elabel} </p>
    {table}
    """
    table_html_template="""
    <table width="95%">
        <colgroup>
            <col span="1" style="width: 70%;">
            <col span="1" style="width: 30%;">
        </colgroup>
    <thead><tr><th width="20%">Property</th><th width="80%">Value</th></tr></thead>
    <tbody>
    {rows}
    </tbody>
    </table>
    """
    row_html_template="""<tr><th>{k}</th><td>{v}</td></tr>"""
    for k,v in entity_data['literals'].items():
        rows.append(row_html_template.format(k=k,v="/".join([str(v.value) for v in v])))

    title = entity_data['node']
    etypes = entity_data['types']
    if etypes is None:
        etypes=[]
    elabels = entity_data.get('labels')
    if elabels is None:
        elabels=[]
    table_html = table_html_template.format(rows="".join(rows))
    panel_html = panel_html_template.format(
                                            title = title,
                                            etype = "/".join([t for t in etypes]),
                                            elabel = "/".join([t.value for t in elabels]), 
                                            table=table_html
                                            )

    return panel_html


def rdflib_graph_to_networkx_for_gravis_original(rdflib_graph, 
                                        ontology_context_graph=None,
                                        hide_types=False, 
                                        hide_literals=False, 
                                        hide_labels=True,
                                        node_colour_scheme=None, 
                                        edge_colour_scheme=None):
    """Construct a networkx graph with annotations matching those used by the gravis visualisation module.
    hide_types controls whether type-like nodes are shown as nodes, or just used as styling cues
    hide_literals controls whether all literal values are projected into the graph, or are attached to nodes property-graph style
    """
    
    n_set, p_set = set(), set()
    types = dict()
    rev_types = dict() # A reverse dictionary node to types
    object_types = dict()
    literals = set()
    entity_data_d=dict() # A dictionary of typed objects
    
    for s,p,o in rdflib_graph.triples((None, None, None)):
        n_set.add(s)
        p_set.add(p)
        n_set.add(o)
        if p in (RDF.type):

            if s not in entity_data_d:
                entity_data_d[s] = graphloader.capture_entity_data(rdflib_graph, s, ontology_context_graph)
            if s not in rev_types:
                rev_types[s] = set([o])
            else:
                rev_types[s].add(o) 

            if o in types:
                types[o].add(s)
            else:
                types[o]=set([s])
                
        if isinstance(o, Literal):
            literals.add(o)
    # Define colour cycles for nodes and edges
    if node_colour_scheme is None:  
        node_colour_scheme = "spectral10"
    if edge_colour_scheme is None:
        edge_colour_scheme = "muted_rainbow10"
    
    n_c_cycle = colourschemes.gen_cycle(node_colour_scheme)
    e_c_cycle = colourschemes.gen_cycle(edge_colour_scheme)    
    n_s_cycle = cycle(['circle', 'rectangle', 'hexagon'])

    types["Untyped"]=set()
    for n in n_set:
        if isinstance(n, URIRef) and n not in rev_types:
            types["Untyped"].add(n)
            entity_data_d[n] = graphloader.capture_entity_data(rdflib_graph, n, ontology_context_graph)


    nx_g = nx.MultiDiGraph()
    # Cycle over Typed Nodes (Entities)
    for t,nodes in types.items():

        tcolor=next(n_c_cycle)
        t_shape = next(n_s_cycle)
        if hide_types and t in (RDF.type):
            # Do not include node in diagram
            pass
        else:
            for n in nodes:
                if isinstance(n, URIRef):
                    # Get Label for Node
                    labels = entity_data_d.get(n).get('labels')
                    if labels is None:
                        labels=[n.n3(rdflib_graph.namespace_manager)]
                    html_packet = construct_property_table(entity_data_d[n])
                    nx_g.add_node(n, label = "/n".join(labels), shape=t_shape, color=tcolor, size=10, click=html_packet)
    # Remaining Nodes are either Literals, or are Untyped Object Nodes
        # Cycle over Literals First.
    for l in literals:
        if not hide_literals:
            label = str(l.value)
            if not isinstance(l.value, pd.Timestamp):
                nx_g.add_node(str(l.value), label=label, shape='circle', color='gray')
            else:
                nx_g.add_edge(s,f"{l.value.isoformat()}",label=label, shape='circle', color='gray')

            #print(l, type(l.value), label)
    # Cycle over Edges
    for p in p_set:
        p_colour = next(e_c_cycle)
        for s,pp,o in rdflib_graph.triples((None, p, None)):
            if hide_types and o in types:
            # Do not add this link as it ends in a type
                pass
            elif hide_literals and o in literals:
                pass
            else:
                labels = entity_data_d.get(pp,{}).get('labels')
                if labels is None:
                    labels=[pp.n3(rdflib_graph.namespace_manager)]
                if isinstance(o, Literal):
                    
                    if not isinstance(o.value, str):
                        if isinstance(o.value, pd.Timestamp):

                            nx_g.add_edge(s,f"{o.value.isoformat()}",label="/".join(labels), shape='circle', color='gray')
                        else:
                            print( o.value, type(o.value))
                            nx_g.add_edge(s,str(o.value),label="/".join(labels), color=p_colour)
                    else:
                        nx_g.add_edge(s,o.value,label="/".join(labels), color=p_colour)
                else:
                    if s==o:
                        print(f"Warning: self-loop detected for {s} with predicate {p}")
                        print((s,pp,o))
                    nx_g.add_edge(s,o,label="/".join(labels), color=p_colour)
                    
    return nx_g



def rdflib_graph_to_networkx_for_gravis(rdflib_graph, 
                                        ontology_context_graph=None,
                                        hide_types=False, 
                                        hide_literals=False, 
                                        hide_labels=True):
    """Construct a networkx graph with annotations matching those used by the gravis visualisation module.
    hide_types controls whether type-like nodes are shown as nodes
    hide_literals controls whether all literal values are projected into the graph, 
    or are attached to nodes property-graph style
    """
    
    n_set, p_set = set(), set()
    types = dict()
    rev_types = dict() # A reverse dictionary node to types
    object_types = dict()
    literals = set()
    entity_data_d=dict() # A dictionary of typed objects
    
    for s,p,o in rdflib_graph.triples((None, None, None)):
        n_set.add(s)
        p_set.add(p)
        n_set.add(o)
        if p in (RDF.type):

            if s not in entity_data_d:
                entity_data_d[s] = graphloader.capture_entity_data(rdflib_graph, s, ontology_context_graph)
            if s not in rev_types:
                rev_types[s] = set([o])
            else:
                rev_types[s].add(o) 

            if o in types:
                types[o].add(s)
            else:
                types[o]=set([s])
                
        if isinstance(o, Literal):
            literals.add(o)

    types["Untyped"]=set()
    for n in n_set:
        if isinstance(n, URIRef) and n not in rev_types:
            types["Untyped"].add(n)
            entity_data_d[n] = graphloader.capture_entity_data(rdflib_graph, n, ontology_context_graph)


    nx_g = nx.MultiDiGraph()
    # Cycle over Typed Nodes (Entities)
    for t,nodes in types.items():

        if hide_types and t in (RDF.type):
            # Do not include node in diagram
            pass
        else:
            for n in nodes:
                if isinstance(n, URIRef):
                    # Get Label for Node
                    labels = entity_data_d.get(n).get('labels')
                    if labels is None:
                        labels=[n.n3(rdflib_graph.namespace_manager)]
                    html_packet = construct_property_table(entity_data_d[n])
                    nx_g.add_node(n, label = "/n".join(labels), click=html_packet, rdfclass=t)
    # Remaining Nodes are either Literals, or are Untyped Object Nodes
        # Cycle over Literals First.
    for l in literals:
        if not hide_literals:
            label = str(l.value)
            if not isinstance(l.value, pd.Timestamp):
                nx_g.add_node(str(l.value), label=label, rdfclass=l.datatype)
            else:
                nx_g.add_node(f"{l.value.isoformat()}",label=label, rdfclass=l.datatype)

            #print(l, type(l.value), label)
    # Cycle over Edges
    for p in p_set:
        
        for s,pp,o in rdflib_graph.triples((None, p, None)):
            if hide_types and o in types:
            # Do not add this link as it ends in a type
                pass
            elif hide_literals and o in literals:
                pass
            else:
                labels = entity_data_d.get(pp,{}).get('labels')
                if labels is None:
                    labels=[pp.n3(rdflib_graph.namespace_manager)]
                if isinstance(o, Literal):
                    
                    if not isinstance(o.value, str):
                        if isinstance(o.value, pd.Timestamp):
                            nx_g.add_edge(s,f"{o.value.isoformat()}",label="/".join(labels),rdfclass=p)
                        else:
                            print( o.value, type(o.value))
                            nx_g.add_edge(s,str(o.value),label="/".join(labels),rdfclass=p)
                    else:
                        nx_g.add_edge(s,o.value,label="/".join(labels),rdfclass=p)
                else:
                    if s==o:
                        print(f"Warning: self-loop detected for {s} with predicate {p}")
                        print((s,pp,o))
                    nx_g.add_edge(s,o,label="/".join(labels),rdfclass=p)
                    
    return nx_g

def decorate_networkx_nodes_with_function(nx_g, node_dec_f):
    """Given a function whose parameters accept a node name, and a dictionary of attributes, 
    and whose return type is a dict, cycle over the available nodes in the graph
    and apply the updated values returned from the function onto the various nodes."""
    for n,d in nx_g.nodes(data=True):
        dec_dict = node_dec_f(n,d)
        for k,v in dec_dict.items():
            nx_g.nodes[n][k]=v
    return nx_g


def decorate_networkx_edges_with_function(nx_g, edge_dec_f):
    """Given a function whose parameters accept an edge name, and a dictionary of attributes, 
    and whose return type is a dict, cycle over the available nodes in the graph
    and apply the updated values returned from the function onto the various nodes."""
    # N.B. The expectation here is that nx_g is a multidigraph
    # i.e. that the details returned from the edge call will contain a key value distinguishing
    #      each individually.
    for s,f,e,d in nx_g.edges(keys=True, data=True):
        dec_dict = edge_dec_f((s,f),d)
        for k,v in dec_dict.items():
            nx_g[s][f][e][k]=v
    return nx_g

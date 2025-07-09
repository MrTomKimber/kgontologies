"""A collection of generic graph visualisation utilities 
   intended to work with gravis and the gravis JSON Graph Format gJGF"""
# https://robert-haas.github.io/gravis-docs/rst/format_specification.html
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, SH
import networkx as nx
import uuid
from itertools import cycle
import colourschemes
import numpy as np

import graphloader


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


def rdflib_graph_to_networkx_for_gravis(rdflib_graph, 
                                        hide_types=False, 
                                        hide_literals=False, 
                                        hide_labels=True,
                                        set_random_node_styles=True,
                                        node_colour_scheme=None, 
                                        edge_colour_scheme=None):
    """Construct a networkx graph with annotations matching those used by the gravis visualisation module.
    hide_types controls whether type-like nodes are shown as nodes, or just used as styling cues
    hide_literals controls whether all literal values are projected into the graph, or are attached to nodes property-graph style
    """
    nx_g = nx.MultiDiGraph()
    n_set, p_set = set(), set()
    types = dict()
    object_types = dict()
    literals = set()
    entity_data_d=dict()
    for s,p,o in rdflib_graph.triples((None, None, None)):
        n_set.add(s)
        p_set.add(p)
        n_set.add(o)
        if p in (RDF.type):

            if s not in entity_data_d:
                entity_data_d[s] = graphloader.capture_entity_data(rdflib_graph, s)

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

    # Cycle over Typed Nodes (Entities)
    for t,nodes in types.items():
        tcolor=next(n_c_cycle)
        t_shape = next(n_s_cycle)
        if hide_types and t in (RDF.type):
            # Do not include node in diagram
            pass
        else:
            for n in nodes:
                # Get Label for Node
                labels = entity_data_d.get(n).get('labels')
                if labels is None:
                    labels=[n.n3(rdflib_graph.namespace_manager)]
                html_packet = construct_property_table(entity_data_d[n])
                nx_g.add_node(n, label = "/".join(labels), shape=t_shape, color=tcolor, size=10, click=html_packet)
    # Remaining Nodes are either Literals, or are Untyped Object Nodes
        # Cycle over Literals First.
    for l in literals:
        if not hide_literals:
            label = l.value
            nx_g.add_node(l, label = label, shape='circle', color='gray')

    # Cycle over Edges
    for p in p_set:
        p_colour = next(e_c_cycle)
        for s,pp,o in rdflib_graph.triples((None, p, None)):
            if hide_types and o in types:
            # Do not add this link as it ends in a type
                pass
            elif hide_literals and o in literals:
                pass
            elif hide_labels and p in (RDFS.label):
                # No need to show labels as separate nodes
                pass
            else:
                labels = entity_data_d.get(pp,{}).get('labels')
                if labels is None:
                    labels=[pp.n3(rdflib_graph.namespace_manager)]
                nx_g.add_edge(s,o,label="/".join(labels), color=p_colour)
    return nx_g

import src.graphloader as graphloader
import src.visgui as visgui
import pandas as pd
from rdflib import Graph, URIRef, Literal
import json

class PyGraph(object):
    def __init__(self, 
                 datafile : str,
                 serialisationjson : str
                 ):
        data_df = pd.read_excel(datafile, na_values='None')
        naming_g = Graph()
        naming_g.parse("../ontologies/kgnaming.owl", format="xml")
        raw_g = graphloader.rdflib_graph_from_dataframe(data_df)
        serial_config = json.load(open(serialisationjson, "r"))
        self.rdf_graph = graphloader.process_anonymous_data_graph(
            raw_g, 
            serial_config
        )
        namespace_dict = serial_config['Namespaces']
        graphloader.bind_namespaces(self.rdf_graph, namespace_dict)

    def gui(self):
        return visgui.gui_visualisation_control(self.rdf_graph).control
    

from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, SH
import pandas as pd
import uuid
import numpy as np
from hashlib import md5
import urllib.parse

def ontology_graph():
    kgdmcar_g = Graph()
    kgdmcar_g.parse ('../ontologies/kgdmcar.owl', format='xml')

    kgnaming_g = Graph()
    kgnaming_g.parse ('../ontologies/kgnaming.owl', format='xml')

    ontology_graph = Graph(bind_namespaces="rdflib")

    for t in kgnaming_g.triples((None, None, None)):
        ontology_graph.add(t)

    for t in kgdmcar_g.triples((None, None, None)):
        ontology_graph.add(t)
    return ontology_graph

def rdflib_graph_from_dataframe(dataframe, data_namespace="http://data#"):
    """Reads in a dataframe and converts it into an anonymous graph"""

    DATA = Namespace(data_namespace)
    g = Graph(bind_namespaces="rdflib")
    g.bind("data", DATA)
    g.add ((DATA.row, RDF.type, OWL.Class))
    g.add ((DATA.row, RDFS.label, Literal("Row")))

    for c in dataframe.columns:
        url_c = urllib.parse.quote(c)
        g.add(( DATA[f"column({url_c})"], RDF.type, OWL.DatatypeProperty )) # Define the column as a datatype property
        g.add(( DATA[f"column({url_c})"], RDFS.label, Literal(c) )) # Attach a simple label to the datatype property
        g.add((DATA.row, DATA.has_field, DATA[f"column({url_c})"]))

    for row_i,data in dataframe.replace({np.nan: None,
                                         pd.NaT: None,
                                         pd.NA: None,
                                         "": None
                                         }).iterrows():
        row_url = DATA[uuid.uuid4().hex]
        row_index = Literal(row_i)
        g.add((row_url, RDF.type, DATA.row))
        g.add((row_url, DATA.row_ident, row_index))
        for c in dataframe.columns:
            url_c = urllib.parse.quote(c)
            p_url = DATA[f"column({url_c})"]
            if data[c] is not None:
                o_literal = Literal(data[c])
                g.add((row_url, p_url, o_literal))
    return g



def process_anonymous_data_graph(data_graph, configuration, data_namespace="http://data#", entity_namespace="http://entity#"):
    DATA = Namespace(data_namespace)
    result_graph = Graph(bind_namespaces="rdflib")
    entity_catalog=dict()
    fqn_catalog=dict()
    hdict = build_naming_lineage_hierarchy(configuration)

    entity_set = set()
    for obj in configuration['NamedObjects']:
        targetclass_uri = URIRef(obj['TargetClass'])
        classbase_uri = URIRef(obj['URIBase'])
        for config_instance in obj['Instances']:
            iname = config_instance['InstanceName']
            subjecttag = config_instance['SubjectTag']
            url_config_subject = urllib.parse.quote(config_instance['SubjectTag'])
            subjecttag_spec = DATA[f"column({url_config_subject})"]
            url_traverse_spec = [urllib.parse.quote(t) for t in traverse_hierarchy_path(hdict, subjecttag)[::-1] if t!="<root>"]
            uqn_tag_spec = [DATA[f"column({t})"] for t in url_traverse_spec]
            entity_catalog[targetclass_uri]=dict()
            
            # Cycle over available data rows
            for datarow in [r[0] for r in data_graph.triples((None, RDF.type, DATA['row']))]:
                # For each datarow, extract instances of targetclass
                #print("Row:" , datarow)
                fetched_label = get_value_from_datarow(datarow, data_graph, subjecttag)
                fqn=get_keylist_from_datarow(datarow, data_graph, uqn_tag_spec)
#                for fetch_key in uqn_tag_spec:
#                    key_values = [r[2] for r in data_graph.triples((datarow, fetch_key, None))]
#                    assert len(key_values)<2
#                    if key_values != []:
#                        fqn.append(key_values[0])
                fqn = ".".join([n for n in fqn if n is not None])
                    
                for instance in [r[2] for r in data_graph.triples((datarow, subjecttag_spec, None))]:
                    newobj = DataNamedObject(targetclass_uri.toPython(), fqn, fetched_label, classbase_uri)

                    if newobj.fully_qualified_name not in fqn_catalog:
                        fqn_catalog[newobj.fully_qualified_name]=newobj
                        entity_catalog[targetclass_uri][newobj.hash]=newobj
                        entity_set.add(newobj)

    #print("##############################")       
    #for k, v in fqn_catalog.items():
    #    print(f"{k} : {v.fully_qualified_name}, {v.label}")
    #print("##############################")       
    relationship_set=set()
    
    for rel in configuration['Relationships']:
        predicate_uri = rel['Predicate']
        for relationship_config_instance in rel['Instances']:
            iname = relationship_config_instance['InstanceName']
            subjecttag = relationship_config_instance['SubjectTag']
            url_traverse_spec = [urllib.parse.quote(t) for t in traverse_hierarchy_path(hdict, subjecttag)[::-1] if t!="<root>"]
            subj_uqn_spec = [DATA[f"column({t})"] for t in url_traverse_spec]

            objecttag = relationship_config_instance['ObjectTag']
            url_traverse_spec = [urllib.parse.quote(t) for t in traverse_hierarchy_path(hdict, objecttag)[::-1] if t!="<root>"]
            obj_uqn_spec = [DATA[f"column({t})"] for t in url_traverse_spec]
            
            for datarow in [r[0] for r in data_graph.triples((None, RDF.type, DATA['row']))]:
                # Test to see if both subject and object values are present (each should be the -1 value in the associated spec)
                raw_subject_fqn=get_keylist_from_datarow(datarow, data_graph, subj_uqn_spec)
                raw_object_fqn=get_keylist_from_datarow(datarow, data_graph, obj_uqn_spec)
                subject_value = get_value_from_datarow(datarow, data_graph, subj_uqn_spec[-1])
                object_value = get_value_from_datarow(datarow, data_graph, obj_uqn_spec[-1])
                                
                if len(raw_subject_fqn)==len(subj_uqn_spec) and len(raw_object_fqn)==len(obj_uqn_spec):
                    subject_fqn=".".join([n for n in raw_subject_fqn if n is not None])
                    object_fqn=".".join([n for n in raw_object_fqn if n is not None])
                    if (subject_value is not None and object_value is not None) and (subject_fqn.strip() != "" and object_fqn.strip() != ""):
                        if subject_fqn in fqn_catalog:
                            subject_entity = fqn_catalog[subject_fqn].uri
                        else:
                            print(datarow, subject_fqn, object_fqn, iname, predicate_uri)
                            assert False
                        if object_fqn in fqn_catalog:
                            object_entity = fqn_catalog[object_fqn].uri
                        else:
                            print(f"{object_fqn} not in fqn_catalog")
                            assert False
                        if subject_entity != object_entity:
                            relationship_set.add(DataRelationship(subject_entity, predicate_uri, object_entity))
                        else:
                            print("**********************************")
                            print("Recursive Relationship")
                            print(predicate_uri)
                            print( f"s{subject_value}, o{object_value}")
                            print(raw_subject_fqn, subj_uqn_spec)
                            print(raw_object_fqn, obj_uqn_spec)
                            print("**********************************")

                elif len(raw_subject_fqn)>0 or len(raw_object_fqn)>0:
                    print("**********************************")
                    print("Size Mismatch")
                    print(predicate_uri)
                    print(raw_subject_fqn, subj_uqn_spec)
                    print(raw_object_fqn, obj_uqn_spec)
                    print("**********************************")
                    

    literals_set=set()
    
    for prop in configuration['Properties']:
        predicate_uri = prop['Predicate']
        for property_config_instance in prop['Instances']:
            iname = property_config_instance['InstanceName']
            subjecttag = property_config_instance['SubjectTag']
            url_traverse_spec = [urllib.parse.quote(t) for t in traverse_hierarchy_path(hdict, subjecttag)[::-1] if t!="<root>"]
            subj_uqn_spec = [DATA[f"column({t})"] for t in url_traverse_spec]

            literaltag = property_config_instance['LiteralTag']
            literaltag_spec = DATA[f"column({urllib.parse.quote(literaltag)})"]
            
            for datarow in [r[0] for r in data_graph.triples((None, RDF.type, DATA['row']))]:
                subject_fqn=".".join([n for n in get_keylist_from_datarow(datarow, data_graph, subj_uqn_spec) if n is not None])
                if subject_fqn.strip() != "":
                    if subject_fqn in fqn_catalog:
                        subject_entity = fqn_catalog[subject_fqn].uri
                    else:
                        print(predicate_uri)
                        print(url_traverse_spec)
                        print(subject_fqn, list(fqn_catalog.keys()))
                        assert False
                    literal_values = [r[2] for r in data_graph.triples((datarow, literaltag_spec, None))]

                    for literal in literal_values:
                        literals_set.add(DataLiteral(subject_entity, predicate_uri, literal))
    # Aggregate the triples into a single list
    triple_collection = [t for e in entity_set for t in e.to_triples() ]
    triple_collection.extend([t for r in relationship_set for t in r.to_triples()])
    triple_collection.extend([t for l in literals_set for t in l.to_triples()])

    return_graph = Graph(bind_namespaces="rdflib")
    for t in triple_collection:
        return_graph.add(t)

    return return_graph

def bind_namespaces(graph, namespace_dict):
    for k,v in namespace_dict.items():
        graph.bind(k,v)

def capture_entity_data(rdflib_graph, entity, ontology_context_graph=None):
    """For a provided rdflib graph and an identified entity, extract
    all types, labels, literals and participating properties"""
    entity_types=None
    entity_labels=None
    entity_literals=dict()
    outbound_entity_properties=dict()
    inbound_entity_properties=dict()
    if ontology_context_graph is None:
        ontology_context_graph=ontology_graph()

    if ontology_context_graph is not None:
        # While this function captures the bare minimum of information about an entity,
        # sometimes, an ontology might define subProperties of RDF.type or RDFS.label
        # that we want to capture as well. 
        label_types = [l[0] for l in ontology_context_graph.query("""
            SELECT ?subtype WHERE {
                ?subtype rdfs:subPropertyOf* rdfs:label .
            }
        """)]

        type_types = [l[0] for l in ontology_context_graph.query("""
            SELECT ?subtype WHERE {
                ?subtype rdfs:subPropertyOf* rdf:type .
            }
        """)]
    else: 
        label_types = [URIRef("http://www.w3.org/2000/01/rdf-schema#label")]
        type_types = [URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://www.w3.org/2002/07/owl#Class")]


    
    for s,p,o in rdflib_graph.triples((entity, RDF.type, None)):
        if entity_types is not None:
            entity_types.add(o)
        else:
            entity_types=set([o])
    for ltype in label_types:
        for s,p,o in rdflib_graph.triples((entity, ltype, None)):
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

def build_naming_lineage_hierarchy(configuration):
    # Step over a kgnamedobject style configuration file and construct a child:parent hierarchy
    # that describes from where an object name's immediate parent is taken.

    # Adopt the convention that if a parenttag returns a Null value, that we populate it with
    # the code <root>
    name_links = dict()
    for obj in configuration['NamedObjects']:
        targetclass = obj['TargetClass']
        for instance in obj['Instances']:
            iname = instance['InstanceName']
            subjecttag = instance['SubjectTag']
            parenttag = instance['ParentTag']
            if parenttag is None or str(parenttag).strip()=="":
                parenttag="<root>"
            name_links[iname]=parenttag
    #for k,v in name_links.items():
    #    print(f"{k} : {v}")
    return name_links

def traverse_hierarchy_path(hdict, start, acc=None):
    # Given a dictionary containing node-to-node parental linkages {child:parent} and a start node,
    # traverse the hierarchy and return the path taken from start node, all the way up the 
    # tree, until it reaches the (local) top.
    if acc is None:
        acc = [start]
    next_value = hdict.get(start)
    if next_value is not None :
        acc.append(next_value)
        traverse_hierarchy_path(hdict, next_value, acc)
    return acc
    
class DataNamedObject(object):
    def __init__(self, type_uri, fully_qualified_name, label, entity_namespace="http://entity#"):
        ENT = Namespace(entity_namespace)
        self.uri = ENT[f"{uuid.uuid4().hex}"].toPython()
        if label is None:
            label = ""
        self.label = label
        self.fully_qualified_name = fully_qualified_name
        if isinstance(type_uri, str):
            self.type = type_uri
        elif isinstance(type_uri, URIRef):
            self.type = type_uri.toPython()
        self.rehash()

    def rehash(self):
        self.hash = md5(".".join([self.label, self.fully_qualified_name, self.type]).encode('utf-8')).hexdigest()
        return self.hash

    def update(self, **properties):
        for k in properties:
            if k in ("label", "description", "type_uri", "fully_qualified_name"):
                print(k, properties[k])
                setattr(self,k,properties[k])
        self.rehash()

    def to_triples(self):
        triples = []
        triples.append((URIRef(self.uri), RDF.type, URIRef(self.type)))
        #triples.append((URIRef(self.uri), URIRef("http://www.semanticweb.org/tomk/ontologies/2025/5/kgnaming#Label"), Literal(self.label)))
        triples.append((URIRef(self.uri), URIRef("http://www.semanticweb.org/tomk/ontologies/2025/5/kgnaming#FullyQualifiedName"), Literal(self.fully_qualified_name)))
        return triples
        
                
    def __repr__(self):
        return f"<NamedObject:{self.type}//{self.fully_qualified_name}>({self.uri})>"

class DataRelationship(object):
    def __init__(self, subject_uri, predicate_uri, object_uri):
        self.subject = subject_uri
        self.predicate = predicate_uri
        self.object = object_uri

    def to_triples(self):
        triples = [[URIRef(self.subject), URIRef(self.predicate), URIRef(self.object)]]
        return triples

    def __repr__(self):
        return f"<Relationship:{self.subject} --{self.predicate}--> {self.object}>"

class DataLiteral(object):
    def __init__(self, subject_uri, predicate_uri, literal):
        self.subject = subject_uri
        self.predicate = predicate_uri
        self.object = literal
        self.rehash()

    def rehash(self):
        self.hash = md5(".".join([self.subject, self.predicate, self.object]).encode('utf-8')).hexdigest()
        return self.hash

    def to_triples(self):
        triples = [[URIRef(self.subject), URIRef(self.predicate), Literal(self.object)]]
        return triples

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.hash == other.hash
        else:
            False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.hash)
    
    def __repr__(self):
        return f"<Literal:{self.subject} --{self.predicate}--> {self.object}>"
    
def get_keylist_from_datarow(rowurl, data_graph, spec):
    fetched_values=[]
    for fetch_key in spec:
        fetched_values.append(get_value_from_datarow(rowurl, data_graph, fetch_key))
    return fetched_values

def get_value_from_datarow(rowurl, data_graph, key):
    fetched_value=None
    key_values = [r[2] for r in data_graph.triples((rowurl, key, None))]
    assert len(key_values)<2
    if key_values != []:
        fetched_value = key_values[0]
    return fetched_value


"""A collection of functions for handling ipywidgets in producing and configuring graph visualisation elements"""


import ipywidgets as widgets
import src.colourschemes as colourschemes
import src.graph_filters as graph_filters
import src.queryaugment as queryaugment
import src.graphvisutils_gravis as graphvisutils_gravis
from src.graphloader import bind_namespaces
import gravis as gv
from IPython.display import display, Image, HTML
from functools import partial
from itertools import cycle
from math import pi, sin, cos



def visualise_scheme(scheme_name, scheme_cols):
    slicelen=100/len(scheme_cols)
    colourspace=list([n*slicelen for n in range(0,len(scheme_cols))])
    svg_content="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100%\" viewBox=\"0 0 100 10\"><defs>{defs}</defs>{content}</svg>"
    css_style_block, style_names=colours_to_css(scheme_cols, style_prefix="stylecolours_"+scheme_name+"__")
    colour_patches=[]
    for e,c in enumerate(scheme_cols):
        colour_patches.append("<rect class=\"{style}\" width=\"{slicelen}\" height=\"100\" x=\"{x_pos}\", y=\"0\" />".format(style=style_names[e], slicelen=slicelen, x_pos=colourspace[e]))
    patch_code = "".join(colour_patches)
    return svg_content.format(content="".join(colour_patches), defs=css_style_block)

def colours_to_css(colours, style_prefix="stylecolours_"):
    style_content_t = """<style> {stylevalues} </style>"""
    style_line_t = " .{name} {{ fill: {col}; stroke: none; stroke-width:0.1;}}"
    style_values_l = []
    style_names = []
    for e,c in enumerate(colours):
        style_values_l.append(style_line_t.format(name=style_prefix+str(e), col=c))
        style_names.append(style_prefix+str(e))
    return style_content_t.format(stylevalues = "\n".join(style_values_l)), style_names

def polygon_points(size, sides, flat=True):
    points = []
    side = (2*pi)/(sides)
    if flat:
        h_side = 0
    else:
        h_side = side/2
        
    for n in range(0, sides):
        a = ((side * n)+h_side)
        x = cos(a) * size
        y = sin(a) * size
        points.append((x,y))
    return points
        
def node_icon(shape, size, area, colour):
    h_area = area/2
    h_size = size/2
    if shape.lower() == "circle" : 
        patch = f"<circle cx=\"{h_area}\" cy=\"{h_area}\" r=\"{h_size}\" fill=\"{colour}\" stroke=\"none\"/>"
    elif shape.lower() == "rectangle" : 
        plist = " ". join([f"{h_area+x},{h_area+y}" for x,y in polygon_points(h_size*1.21,4, False)])
        patch = f"<polygon points=\"{plist}\" fill=\"{colour}\" stroke=\"none\" />"
    elif shape.lower() == "hexagon" : 
        plist = " ". join([f"{x+h_area},{y+h_area}" for x,y in polygon_points(h_size,6, True)])
        patch = f"<polygon points=\"{plist}\" fill=\"{colour}\" stroke=\"none\" />"
        
    svg_content="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100%\" viewBox=\"0 0 100 100\">{content}</svg>"

    return svg_content.format(content=patch)


class gui_scheme_picker_multi_control(object):
    def __init__(self, schemes_d):
        self.schemes = schemes_d
        self.render_cols=[]

        for k,v in self.schemes.items():
            self.render_cols.append(visualise_scheme(k,v))

        style = {'description_width': 'initial'}

        self.dropdown = widgets.Dropdown(
                    options=self.schemes.keys(), 
                    value = list(self.schemes.keys())[0], 
                    description='Colour Scheme', 
                    disabled=False, 
                    style=style
                )
        self.value=self.dropdown.value
        self.graphic = widgets.HTML(layout={'width':"40%"},
                 value=self.render_cols[0])
        self.dropdown.observe(self.on_dropdown_change, names='index')

        self.control = widgets.VBox(children=[self.dropdown, self.graphic], layout={'width':"100%"})

    def on_dropdown_change(self, change):
        
        self.graphic.value=self.render_cols[change['owner'].index]
        self.value=self.dropdown.value

    def update(self, value):
        if value in self.schemes:
            self.dropdown.value = value
        else:
            raise KeyError


class gui_node_styletab_control(object):
    def __init__(self, **default_kwargs):
        self.implemented_kwarg_list = ['theme','shape','size','colour','name', 'id']

        for k,v in default_kwargs.items():
            if k in self.implemented_kwarg_list:
                if k.lower()=="shape":
                    self.shape_value=v
                elif k.lower()=="size":
                    self.size_value=v
                elif k.lower()=="colour":
                    self.colour_value=v
                elif k.lower()=="name":
                    self.name=v
                elif k.lower()=="id":
                    self.id=v

        self._ui_shape_selector_dropdown = widgets.Dropdown(
                    options=["Circle", "Rectangle", "Hexagon"], 
                    value = self.shape_value, 
                    description='Shape', 
                    disabled=False
                    )

        self._ui_node_size_selector = widgets.IntSlider(
            value = self.size_value, 
            min=5, 
            max=100,
            step=5,
            description="Size", 
            disabled=False
        )

        self._ui_node_colour_selector = widgets.ColorPicker(
            concise=False, 
            description="Colour", 
            value=self.colour_value, 
            disabled=False
        )

        self._ui_node_icon_preview_html = widgets.HTML(
            value = node_icon(shape=self.shape_value, 
                            size=self.size_value,
                            area = 100,
                            colour=self.colour_value),
            layout = widgets.Layout(width="10%")
        )

        self._ui_v_box = widgets.VBox(children=[self._ui_shape_selector_dropdown, 
                                               self._ui_node_size_selector, 
                                               self._ui_node_colour_selector])
        
        self._ui_h_box = widgets.HBox(children=[self._ui_node_icon_preview_html, self._ui_v_box])
        self._ui_title = widgets.HTML(
            value=f"<h1>{self.name}</h1>", 
            placeholder = f"{self.name}"
        )
        self._ui_v_container = widgets.VBox(children=[self._ui_title, self._ui_h_box])
        self._ui_shape_selector_dropdown.observe(self.on_update, names='value')
        self._ui_node_size_selector.observe(self.on_update, names='value')
        self._ui_node_colour_selector.observe(self.on_update, names='value')

        self.control = self._ui_v_container
        self.colour_unchanged = True
        self.shape_value=self._ui_shape_selector_dropdown.value
        self.size_value=self._ui_node_size_selector.value
        self.colour_value=self._ui_node_colour_selector.value
        self.selected_value=True  # Default not yet implemented
        self.label_size_value=20  # Default not yet implemented

    def on_update(self, change):
        
        self.shape_value=self._ui_shape_selector_dropdown.value
        self.size_value=self._ui_node_size_selector.value

        self.colour_value=self._ui_node_colour_selector.value

        self._ui_node_icon_preview_html.value=node_icon(shape=self.shape_value, 
                                size=self.size_value, 
                                area = 100,
                                colour=self.colour_value)
        


    def update(self, **kwargs):
        
        for k,v in kwargs.items():
            if k in self.implemented_kwarg_list:
                if k.lower()=="shape":
                    if v in self._ui_shape_selector_dropdown.options:
                        self._ui_shape_selector_dropdown.value=v
                        self.shape_value=v
                    else:
                        pass
                elif k.lower()=="size":
                    self._ui_node_size_selector.value=v
                    self.size_value=v
                elif k.lower()=="colour":
                    self._ui_node_colour_selector.value=v
                    self.colour_value=v


class gui_rdfgraph_node_styler_controls(object):

    def __init__(self, graph, default_scheme='dutch9', default_size=20, default_label_size=10, debug=False):
        self.schemes_d = colourschemes.colour_schemes
        self.graph = graph
        self._ui_theme_picker = gui_scheme_picker_multi_control(self.schemes_d)
        self.theme = self._ui_theme_picker.value
        self.type_dict = dict(sorted(graph_filters.gen_types_filter_template(graph, sparql_method=True).items(), key=lambda x : x[0]))
        self.shape_scheme = ["Circle", "Rectangle", "Hexagon"]
        initial_type_style_mapping=self.create_type_style_mapping(
                                                                  type_dict=self.type_dict, 
                                                                  colour_scheme=self.theme, 
                                                                  default_size=default_size, 
                                                                  default_label_size=default_label_size, 
                                                                  shape_scheme=self.shape_scheme)
        
        self.style_tab_collection=[]

        for k,v in initial_type_style_mapping.items():
            self.style_tab_collection.append(gui_node_styletab_control(**v))

        self._ui_type_style_tab = widgets.Tab(  titles=[c.name for c in self.style_tab_collection], 
                                                children=[c.control for c in self.style_tab_collection])
        self._ui_theme_picker.dropdown.observe(self.on_theme_change, names="value")
        
        self.debug = widgets.Output()
        if debug:
            self.control = widgets.VBox(children=[self._ui_theme_picker.control, self._ui_type_style_tab, self.debug])
        else:
            self.control = widgets.VBox(children=[self._ui_theme_picker.control, self._ui_type_style_tab])


    def create_type_style_mapping(self, type_dict, colour_scheme, default_size, default_label_size, shape_scheme):

        colour_cycle = colourschemes.gen_cycle(colour_scheme)
        shape_cycle = cycle(shape_scheme)
        cycle_period = len(colourschemes.get_colour_scheme(colour_scheme))
        p = 0
        type_style_mapping = dict()
        s = next(shape_cycle)
        for k,v in type_dict.items():
            p = p + 1
            c = next(colour_cycle)
            if p > cycle_period:
                s = next(shape_cycle)
                p=0
            
            type_style_mapping[k] = {        "id" : k, 
                                             "name" : k.n3(self.graph.namespace_manager), 
                                             "shape" : s, 
                                             "size" : default_size, 
                                             "colour" : c, 
                                             "color" : c, 
                                             "selected" : v, 
                                             "label_size" : default_label_size}
        return type_style_mapping
    
    def get_typed_mappings(self):
        # See: https://robert-haas.github.io/gravis-docs/rst/format_specification.html#gjgf-format
        mappings_d = dict()
        for style in self.style_tab_collection:
            mappings_d[style.id]={"id" : style.id, 
                                  "name" : style.name, 
                                  "shape" : str(style.shape_value).lower(), 
                                  "size" : style.size_value, 
                                  "color" : style.colour_value, 
                                  "selected" : style.selected_value, 
                                  "label_size" : style.label_size_value}
        return mappings_d



    def on_theme_change(self, change):
        #with self.debug:
        #    print(change)
        self.theme=change['new']
        type_style_mappings=self.create_type_style_mapping(
                                                          type_dict=self.type_dict, 
                                                          colour_scheme=self.theme,
                                                          default_size=30, 
                                                          default_label_size=20, 
                                                          shape_scheme=self.shape_scheme
                                                          )
        for style_tab in self.style_tab_collection:

            if style_tab.id in type_style_mappings:
                update_dict = {k:v for k,v in type_style_mappings[style_tab.id].items() if k in {"colour", "size", "shape"}}
                style_tab.update(**update_dict)

class gui_rdfgraph_nodetype_filter_control(object):
    def __init__(self, graph):
        self.graph = graph
        self.type_dict = {k.n3(self.graph.namespace_manager):k for k,v in sorted(graph_filters.gen_types_filter_template(graph, sparql_method=True).items(), key = lambda x : x[0])}

        
        self._ui_type_selector = widgets.SelectMultiple(
                            options=list(self.type_dict.keys()),
                            value=list(self.type_dict.keys()),
                            description='Types',
                            disabled=False, 
                            rows=len(list(self.type_dict.keys())),
                            layout=widgets.Layout(width="70%")
                            )
        
        self.control = self._ui_type_selector
        
    def get_selected_uris(self):
        rlist = []
        for u in self.control.value:
            rlist.append(self.type_dict.get(u))
        return rlist
    
    def get_all_possible_uris(self):
        rlist = []
        for u in self.control.options:
            rlist.append(self.type_dict.get(u))
        return rlist

class gui_rdfgraph_predicate_filter_control(object):
    def __init__(self, graph):
        self.graph = graph
        self.pred_dict = {k.n3(self.graph.namespace_manager):k for k,v in sorted(graph_filters.gen_predicate_filter_template(graph, sparql_method=True).items(), key = lambda x : x[0])}

        
        self._ui_pred_selector = widgets.SelectMultiple(
                            options=list(self.pred_dict.keys()),
                            value=list(self.pred_dict.keys()),
                            description='Predicates',
                            disabled=False, 
                            rows=len(list(self.pred_dict.keys())),
                            layout=widgets.Layout(width="70%")
                            )
        
        self.control = self._ui_pred_selector

    def get_selected_uris(self):
        rlist = []
        for u in self.control.value:
            rlist.append(self.pred_dict.get(u))
        return rlist
    
    def get_all_possible_uris(self):
        rlist = []
        for u in self.control.options:
            rlist.append(self.pred_dict.get(u))
        return rlist
        

class gui_visualisation_control(object):
    def __init__(self, graph, debug=False):
        self.graph = graph

        # Load and bind associated ontologies for additional data enrichment
        

        self.type_filter = gui_rdfgraph_nodetype_filter_control(graph)
        self.node_styler = gui_rdfgraph_node_styler_controls(graph)
        self.pred_filter = gui_rdfgraph_predicate_filter_control(graph)
        self.pred_styler = gui_rdfgraph_predicate_styler_controls(graph)

        self.vis_graph_settings = {
            "node_label_data_source" : "label", 
            "node_size_data_source" : "size", 
            "node_label_size_factor" : 1.5, 
            "node_size_factor" : 1.0, 
            "edge_size_data_source" : "size", 
            "edge_label_data_source" : "label", 
            "edge_size_factor" : 2.5, 
            "show_edge_label" : True,
            "edge_curvature" : 0.2,
            "graph_height" : 800,
            "details_height" : 300, 
            "layout_algorithm" : "forceAtlas2Based", 
            #"layout_algorithm" : "hierarchicalRepulsion", 
            #"gravitational_constant" : -0.15, 
            "central_gravity" : 2.0, 
            "spring_constant" : 0.14,
            "avoid_overlap" : 0.5
            
        }

        self.d3_graph_settings = {
            "node_label_data_source" : "label", 
            "node_size_data_source" : "size", 
            "edge_size_data_source" : "size", 
            "edge_label_data_source" : "label", 
            "show_edge_label" : True,
            "edge_curvature" : 0.2,
            "use_collision_force" : True, 
            "collision_force_radius" : 60, 
            "collision_force_strength" : 0.8,
            "graph_height" : 800,
            "details_height" : 300, 
            
        }

        self._ui_output_canvas = widgets.Output()
        
        self.generate_vis_button = widgets.Button(
            description="Generate Visualisation", 
            disabled=False, 
            button_style='',
            layout=widgets.Layout(width="20%"),
            tooltip="Generate Visualisation"
        )
        self.generate_vis_button.on_click(self.generate_visualisation)

        accordion = widgets.Accordion(children=[self.type_filter.control, 
                                        self.node_styler.control,
                                       self.pred_filter.control, 
                                       self.pred_styler.control],
                                      titles=["Type Filter", 
                                      "Style Nodes", 
                                      "Predicate Filter",
                                      "Style Predicates"])
        
        
        user_layout = widgets.VBox([accordion, self.generate_vis_button, self._ui_output_canvas], 
                                   layout=widgets.Layout(width="100%"))
        
        self.control = user_layout
        self.generate_visualisation(self.generate_vis_button)
        

    def generate_visualisation(self, b):

        # Get updated filter details
        exclude_types = set(self.type_filter.get_all_possible_uris())-set(self.type_filter.get_selected_uris())
        exclude_preds = set(self.pred_filter.get_all_possible_uris()) - set(self.pred_filter.get_selected_uris())
        exclude_nodes = set() ## Not implemented

        # Apply new filters to regenerate display graph
        new_g = queryaugment.filter_triples_from_graph(self.graph, exclude_nodes, exclude_preds, exclude_types)
        # Rebind any namespaces to graph
        namespace_dict = {k:v for k,v in self.graph.namespace_manager.namespaces()}
        bind_namespaces(new_g, namespace_dict)
        # Apply styling choices to graph

        nx_g = graphvisutils_gravis.rdflib_graph_to_networkx_for_gravis(new_g, 
                                                                ontology_context_graph=None, 
                                                                hide_types=True, 
                                                                hide_literals=True)
        type_mapping_d = self.node_styler.get_typed_mappings()
        pred_mapping_d = self.pred_styler.get_typed_mappings()
        
        ndf = partial(node_decorator_function, type_mapping=type_mapping_d)
        pdf = partial(edge_decorator_function, pred_mapping=pred_mapping_d)
        nx_g = graphvisutils_gravis.decorate_networkx_nodes_with_function(nx_g, ndf)
        nx_g = graphvisutils_gravis.decorate_networkx_edges_with_function(nx_g, pdf)
        self.nx_g = nx_g
        # Generate Figure
        fig = gv.vis(nx_g, **self.vis_graph_settings)
        # Apply figure to output canvas
        self._ui_output_canvas.clear_output()
        with self._ui_output_canvas:
            display(HTML(fig.to_html_partial()))

        return new_g, nx_g, fig

def node_decorator_function(node, data, type_mapping):
    """A function for updating node decoration details based on type and/or other information.
    Common node attributes to target for updation are:
        color
        size
        shape
        """
    return_d = dict()

    for k,v in type_mapping.items():
        if data.get("rdfclass") in type_mapping.keys():
            for mk,mv in type_mapping[data["rdfclass"]].items():
                if mk in {"shape", "size", "color", "opacity", "border_color", "border_size", 
                          "label_color", "label_size"}:
                    return_d[mk]=mv
    return return_d

def edge_decorator_function(edge, data, pred_mapping):
    """A function for updating node decoration details based on type and/or other information.
    Common node attributes to target for updation are:
        color
        size
        shape
        """
    return_d = dict()

    for k,v in pred_mapping.items():
        if data.get("rdfclass") in pred_mapping.keys():
            for mk,mv in pred_mapping[data["rdfclass"]].items():
                if mk in {"shape", "size", "color", "opacity", "border_color", "border_size", 
                          "label_color", "label_size"}:
                    return_d[mk]=mv
    return return_d

def predicate_icon(size, area, colour):
    h_area = area/2
    h_size = size/2
    size = size / 10
    patch = f"""<path d=\"M {-(2/3*size)} 0 
                          l 8 0 
                          l -1 -2 
                          l 8 2 
                          l -8 2 
                          l 1 -2 
                          Z\" 
                          fill=\"{colour}\" 
                          stroke=\"{colour}\" 
                          stroke-width=\"{size}\" 
                          stroke-linejoin=\"miter\" 
                          stroke-miterlimit=\"10\"/>"""
        
    svg_content="<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100%\" viewBox=\"-2 -10 24 18\">{content}</svg>"

    return svg_content.format(content=patch)


class gui_predicate_styletab_control(object):
    def __init__(self, **default_kwargs):
        self.implemented_kwarg_list = ['theme','size','colour','name', 'id']

        for k,v in default_kwargs.items():
            if k in self.implemented_kwarg_list:
                if k.lower()=="size":
                    self.size_value=v
                elif k.lower()=="colour":
                    self.colour_value=v
                elif k.lower()=="name":
                    self.name=v
                elif k.lower()=="id":
                    self.id=v

        self._ui_predicate_size_selector = widgets.IntSlider(
            value = self.size_value, 
            min=1, 
            max=15,
            step=1,
            description="Size", 
            disabled=False
        )

        self._ui_predicate_colour_selector = widgets.ColorPicker(
            concise=False, 
            description="Colour", 
            value=self.colour_value, 
            disabled=False
        )

        self._ui_predicate_icon_preview_html = widgets.HTML(
            value = predicate_icon(
                            size=self.size_value,
                            area = 100,
                            colour=self.colour_value),
            layout = widgets.Layout(width="10%")
        )



        self._ui_v_box = widgets.VBox(children=[
                                               self._ui_predicate_size_selector, 
                                               self._ui_predicate_colour_selector])

        #self.debug = widgets.Output()
        
        self._ui_h_box = widgets.HBox(children=[self._ui_predicate_icon_preview_html, self._ui_v_box])
        self._ui_title = widgets.HTML(
            value=f"<h1>{self.name}</h1>", 
            placeholder = f"{self.name}"
        )
        self._ui_v_container = widgets.VBox(children=[self._ui_title, self._ui_h_box])
        #with self.debug:
        #    print("set update function")

        self._ui_predicate_size_selector.observe(self.on_control_update, names='value')
        self._ui_predicate_colour_selector.observe(self.on_control_update, names='value')
        
        self.control = self._ui_v_container
        self.selected_value=True  # Default not yet implemented
        self.label_size_value=20  # Default not yet implemented



    def on_control_update(self, change):
        #with self.debug:
        #    print("on_update")
        #    print(change)
        self.size_value=self._ui_predicate_size_selector.value
        self.colour_value=self._ui_predicate_colour_selector.value
        self._ui_predicate_icon_preview_html.value=predicate_icon(
                                size=self.size_value, 
                                area = 100,
                                colour=self.colour_value)
        


    def update(self, **kwargs):
        
        for k,v in kwargs.items():
            if k in self.implemented_kwarg_list:
                if k.lower()=="size":
                    self._ui_predicate_size_selector.value=v
                    self.size_value=v
                elif k.lower()=="colour":
                    self._ui_predicate_colour_selector.value=v
                    self.colour_value=v


class gui_rdfgraph_predicate_styler_controls(object):

    def __init__(self, graph, default_scheme='dutch9', default_size=2, default_label_size=10, debug=False):
        self.schemes_d = colourschemes.colour_schemes
        self.graph = graph
        self._ui_theme_picker = gui_scheme_picker_multi_control(self.schemes_d)
        self.theme = self._ui_theme_picker.value
        #self.pred_dict = {k.n3(self.graph.namespace_manager):k for k,v in sorted(graph_filters.gen_predicate_filter_template(graph, sparql_method=True).items(), key = lambda x : x[0])}
        self.pred_dict = dict(sorted(graph_filters.gen_predicate_filter_template(graph, sparql_method=True).items(), key = lambda x : x[0]))
        
        initial_type_style_mapping=self.create_predicate_style_mapping(
                                                                  pred_dict=self.pred_dict, 
                                                                  colour_scheme=self.theme, 
                                                                  default_size=default_size, 
                                                                  default_label_size=default_label_size)
        
        self.style_tab_collection=[]

        for k,v in initial_type_style_mapping.items():
            self.style_tab_collection.append(gui_predicate_styletab_control(**v))

        self._ui_type_style_tab = widgets.Tab(  titles=[c.name for c in self.style_tab_collection], 
                                                children=[c.control for c in self.style_tab_collection])
        self._ui_theme_picker.dropdown.observe(self.on_theme_change, names="value")
        
        self.debug = widgets.Output()
        if debug:
            self.control = widgets.VBox(children=[self._ui_theme_picker.control, self._ui_type_style_tab, self.debug])
        else:
            self.control = widgets.VBox(children=[self._ui_theme_picker.control, self._ui_type_style_tab])


    def create_predicate_style_mapping(self, pred_dict, colour_scheme, default_size, default_label_size):
        
        colour_cycle = colourschemes.gen_cycle(colour_scheme)
        pred_style_mapping = dict()
        
        for k,v in pred_dict.items():
            c = next(colour_cycle)
            pred_style_mapping[k] = {        "id" : k, 
                                             "name" : k.n3(self.graph.namespace_manager), 
                                             "size" : default_size, 
                                             "colour" : c, 
                                             "color" : c, 
                                             "border_color" : c, 
                                             "border_size" : 1, 
                                             "label_size" : default_label_size}
        
        return pred_style_mapping
    
    def get_typed_mappings(self):
        # See: https://robert-haas.github.io/gravis-docs/rst/format_specification.html#gjgf-format
        mappings_d = dict()
        for style in self.style_tab_collection:
            mappings_d[style.id]={"id" : style.id, 
                                  "name" : style.name, 
                                  "size" : style.size_value, 
                                  "color" : style.colour_value, 
                                  "label_size" : style.label_size_value}
        return mappings_d



    def on_theme_change(self, change):
        with self.debug:
            print(change)
        self.theme=change['new']
        predicate_style_mappings=self.create_predicate_style_mapping(
                                                          pred_dict=self.pred_dict, 
                                                          colour_scheme=self.theme,
                                                          default_size=2, 
                                                          default_label_size=20
                                                          )
        for style_tab in self.style_tab_collection:

            if style_tab.id in predicate_style_mappings:
                update_dict = {k:v for k,v in predicate_style_mappings[style_tab.id].items() if k in {"colour", "size", "shape"}}
                style_tab.update(**update_dict)
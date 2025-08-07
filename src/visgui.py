"""A collection of functions for handling ipywidgets in producing and configuring graph visualisation elements"""


import ipywidgets as widgets
import src.colourschemes as colourschemes
import src.graph_filters as graph_filters
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
        print(change)
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

        self._ui_shape_selector_dropdown.observe(self.on_update, names='value')
        self._ui_node_size_selector.observe(self.on_update, names='value')
        self._ui_node_colour_selector.observe(self.on_update, names='value')

        self.control = self._ui_h_box
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
        print(kwargs)
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
                                             "selected" : v, 
                                             "label_size" : default_label_size}
        return type_style_mapping
    
    def get_typed_mappings(self):
        # See: https://robert-haas.github.io/gravis-docs/rst/format_specification.html#gjgf-format
        mappings_d = dict()
        for style in self.style_tab_collection:
            mappings_d[style.id]={"id" : style.id, 
                                  "name" : style.name, 
                                  "shape" : style.shape_value, 
                                  "size" : style.size_value, 
                                  "colour" : style.colour_value, 
                                  "selected" : style.selected_value, 
                                  "label_size" : style.label_size_value}
        return mappings_d



    def on_theme_change(self, change):
        with self.debug:
            print(change)
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


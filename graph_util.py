from graph_tool.all import *
import pandas as pd


def from_files():
    print("sh")


def load_nodes(g, file_path, sep='\t'):
    nodes_dataframe = pd.read_csv(file_path, encoding='utf-8', sep=sep, index_col='id')
    id_prop = g.new_vertex_property('object')
    g.vp.id = id_prop  # equivalent to g.vertex_properties['id'] = id_prop
    id_dic = {}

    for col in nodes_dataframe.columns:
        col_prop = g.new_vertex_property('object')
        g.vp[col] = col_prop

    for index, row in nodes_dataframe.iterrows():
        v = g.add_vertex()
        id_dic[index] = v
        for col in nodes_dataframe.columns:
            g.vp[col][v] = row[col]

    # Adding the ids dictionary as a graph property named 'id_dic'
    id_dic_prop = g.new_graph_property('object')
    g.gp['id_dic'] = id_dic_prop
    g.gp.id_dic = id_dic
    return g


def load_edges(g, file_path, sep='\t'):
    edges_dataframe = pd.read_csv(file_path, encoding='utf-8', sep=sep, index_col=['src_id', 'dest_id'])
    edges_dataframe.sortlevel(inplace=True)

    weight_prop = g.new_edge_property("object")
    g.ep['weight'] = weight_prop

    for col in edges_dataframe.columns:
        col_prop = g.new_edge_property('object')
        g.ep[col] = col_prop

    for index, row in edges_dataframe.iterrows():
        source_vertex = g.gp.id_dic[index[0]]
        end_vertex = g.gp.id_dic[index[1]]
        e = g.edge(g.vertex_index[source_vertex], g.vertex_index[end_vertex])
        if e is None:
            e = g.add_edge(source_vertex, end_vertex)
            g.ep.weight[e] = 1
            for col in edges_dataframe.columns:
                g.ep[col][e] = row[col]

        else:
            g.ep.weight[e] = g.ep.weight[e] + 1
    return g


def load_messages(g, file_path, sep='\t'):
    messages_dataframe = pd.read_csv(file_path, encoding='utf-8', sep=sep, index_col='id')
    messages_prop = g.new_graph_property('object')
    g.gp['messages'] = messages_prop
    g.gp.messages = messages_dataframe
    return g


def load_graph(directed,
               nodes_file_path,
               edges_file_path,
               messages_file_path=None,
               sep='\t'
               ):
    g = Graph()
    if not directed:
        g.set_directed(False)

    load_nodes(g, nodes_file_path, sep)
    load_edges(g, edges_file_path, sep)
    if messages_file_path is not None:
        load_messages(g, messages_file_path, sep)
    return g


# g = load_graph(True, 'input/nodes.txt', 'input/edges.txt', 'input/messages.txt', sep='\t')
# print('done')

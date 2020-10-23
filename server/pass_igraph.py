import json
from test import NetWork
from igraph import EdgeSeq, Graph
import random


g1 = NetWork('bolt://localhost:7687', 'neo4j', '123')
a = g1.get_all_edges()


def get_TupleList(inclist):
    tp = []
    for i in range(len(inclist)):
        tp.append({i: inclist[i]})
    return tp


gr = []

for e in a:
    gr.append((e[2].start_node['name'], e[2].end_node['name'], e[2].type))

g = Graph.TupleList(gr, directed=True, weights=True)


def get_cluster(cluster, node):
    for i in range(len(cluster)):
        if node in cluster[i]:
            return i


def get_color(cluster):
    color = []
    for _ in range(len(cluster)):
        random_number = random.randint(0, 16777215)
        hex_number = str(hex(random_number))
        hex_number = '0x' + hex_number[2:]
        color.append(hex_number)
    return color


cluster = list(g.components(mode="WEAK"))

def gen_json(g):
    graph = {"nodes": [], "edges": []}
    clr_list = get_color(cluster)
    for node in g.vs:
        idx = node.index
        inf = {"id": idx, "label": node['name'],
               "x": 0, "y": 0, "color": clr_list[get_cluster(cluster, idx)]}
        graph['nodes'].append(inf)
    for edge in g.es:
        inf = {"id": edge.index, "source": edge.source,
               "target": edge.target, "value": 2}
        graph['edges'].append(inf)
    return graph


def save_json(g):
    with open("../visualization/data.json", 'w+') as f:
        json.dump(gen_json(g), f)


save_json(g)

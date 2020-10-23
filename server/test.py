from neo4j import GraphDatabase
from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
import json
from numpy.random import randint


class NetWork:
    def __init__(self, uri, user, passwd):
        self.driver = GraphDatabase.driver(uri, auth=(user, passwd))

    def get_all_edges(self):
        query = (
            """
            MATCH (n)-[r]->(m) RETURN n, m, r LIMIT 8000
            """
        )

        with self.driver.session() as session:
            a = session.run(query).values()
        return a

    def get_all_nodes(self):
        query = (
            """
            MATCH (n) RETURN (n)
            """
        )
        with self.driver.session() as session:
            return session.run(query).values()

    def get_node_with_n_edge(self, n):
        query = (
            """
            MATCH (m)-[r]->(n)
            WITH n, m, count(r) as rel_cnt
            WHERE rel_cnt>={}
            RETURN m, n
            """
        ).format(n)
        with self.driver.session() as session:
            return session.run(query).values()

    def get_edge_with_n_edge(self, n):
        query = (
            """
            MATCH (m)-[r]->(n)
            WITH r, count(r) as rel_cnt
            WHERE rel_cnt>={}
            RETURN r
            """
        ).format(n)
        with self.driver.session() as session:
            return session.run(query).values()


def export_json(edge_list):
    gr = {"nodes": [], "edges": []}
    start_node = []
    end_node = []
    for b in edge_list:
        start_node.append(b[0])
        end_node.append(b[1])
        rel = b[2]
        gr['edges'].append({'id': rel.id, "source": b[0].id,
                            "target": b[1].id, "value": 1, "type": rel.type})

    node_list = list(set(start_node).union(set(end_node)))
    for i in range(len(node_list)):
        gr['nodes'].append({"id": node_list[i].id, "label": node_list[0]
                            ['name'], "x": 0, "y": 0, "size": 2})
    with open('../visualization/data.json', 'w+') as f:
        json.dump(gr, f)


uri = 'bolt://localhost:7687'

g = NetWork(uri, 'neo4j', '123')



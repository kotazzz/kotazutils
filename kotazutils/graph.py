from random import randint, choice
class Graph:
    #! Moved to kotazutils.graph
    # TODO: update to new version of graph
    def __init__(self):
        self.graph = {}

    def add_vertex(self, vertex):
        if vertex in self.graph:
            raise Exception('Vertex {} already exists'.format(vertex))
        self.graph[vertex] = []

    def add_edge(self, vertex1, vertex2):
        self.graph[vertex2].append(vertex1)
        self.graph[vertex1].append(vertex2)
        return
        raise Exception(
            'Edge already exists: {} and {}'.format(vertex1, vertex2))

    def add_connected(self, vertex1, new_vertex):
        self.add_vertex(new_vertex)
        self.add_edge(vertex1, new_vertex)
        self.add_edge(new_vertex, vertex1)

    def get_neighbors(self, vertex):
        if vertex not in self.graph:
            raise Exception('Vertex {} not exists'.format(vertex))
        return [i for i in self.graph[vertex] if i != vertex]

    def get_vertices(self):
        return list(self.graph.keys())

    def edge_random_for_vertex(self, vertex):
        if vertex not in self.graph:
            raise Exception('Vertex {} not exists'.format(vertex))
        if len(self.graph[vertex]) == 0:
            return
        vertices = self.get_vertices()
        vertex2 = choice(
            [vertex2 for vertex2 in vertices if vertex != vertex2])
        self.add_edge(vertex, vertex2)
        return vertex2

    def edge_random(self):
        vertices = self.get_vertices()
        vertex1 = choice(vertices)
        vertex2 = choice([vertex for vertex in vertices if vertex != vertex1])
        self.add_edge(vertex1, vertex2)
        return vertex1, vertex2

    def to_matrix(self):
        vertices = self.get_vertices()
        matrix = []
        for vertex in vertices:
            matrix.append([])
            for vertex2 in vertices:
                if vertex2 in self.graph[vertex]:
                    matrix[-1].append(1)
                else:
                    matrix[-1].append(0)
        return matrix

    def __str__(self):
        return str(self.graph)
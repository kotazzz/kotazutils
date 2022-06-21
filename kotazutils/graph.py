from random import randint, choice

class Graph:
    def __init__(self):
        self.graph = {}
    
    def add_vertex(self, vertex):
        self.graph[vertex] = []

    def add_edge(self, vertex1, vertex2):
        if not vertex1 in self.graph[vertex2]:
            self.graph[vertex2].append(vertex1)
        if not vertex2 in self.graph[vertex1]:
            self.graph[vertex1].append(vertex2)
        
        

    def get_neighbors(self, vertex):
        return self.graph[vertex]

    def get_vertices(self):
        return list(self.graph.keys())

    def edge_random(self):
        vertices = self.get_vertices()
        vertex1 = choice(vertices)
        vertex2 = choice([vertex for vertex in vertices if vertex != vertex1])
        self.add_edge(vertex1, vertex2)
        return vertex1, vertex2

    def edge_random_percent(self, percent):
        vertices = self.get_vertices()
        for vertex1 in vertices:
            for vertex2 in vertices:
                if randint(0, 100) < percent:
                    self.add_edge(vertex1, vertex2)

    def __str__(self):
        return str(self.graph)

    def edge_random_n(self, n):
        for i in range(n):
            self.edge_random()

    def edge_random_n_percent(self, n, percent):
        for i in range(n):
            if randint(0, 100) < percent:
                self.edge_random()
    
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
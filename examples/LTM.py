import random

from graph_tool.generation import geometric_graph, price_network

import base
import numpy as np

g = price_network(2000)

weight_prop = g.new_edge_property('object')
g.ep['weight'] = weight_prop

threshold_prop = g.new_vertex_property('object')
g.vp['threshold'] = threshold_prop

active_prop = g.new_vertex_property('bool')
g.vp['active'] = active_prop

color_prop = g.new_vertex_property('vector<double>')
g.vp['color'] = color_prop


class LTM(base.Model):
    def __init__(self, g, agent_class, connection_class):
        super().__init__(g, agent_class, connection_class)

    def select(self):
        return [a for a in self.agents if self.g.vp.active[a.v] == False], None

    def agent_action(self, agent):
        inner_sum = sum([self.g.ep.weight[e] for e in agent.v.in_edges() if self.g.vp.active[e.source()] == True])
        if inner_sum > self.g.vp.threshold[agent.v]:
            event = base.Event(self, base.EventType.AGENT_V, 'active', True, agent.v)
            self.timeline.add_event(self.now + 1, event)

    def should_stop(self):
        return self.now >= 10000

    def update_entity_viz(self, event_type, entity):
        if event_type == base.EventType.AGENT_V:
            if self.g.vp.active[entity]:
                self.g.vp.color[entity] = [0, 0, 0, 1]

    def number_active_nodes(self):
        return sum(1 for a in self.agents if self.g.vp.active[a.v] == True)


class LTM_Agent(base.Agent):
    def __init__(self, v):
        super().__init__(v)
        g.vp.active[v] = False

        g.vp.threshold[v] = np.random.random()  # TODO: change to normal
        in_edges_size = len(list(v.in_neighbours()))

        random_numbers = np.random.random(in_edges_size)
        random_numbers = random_numbers / sum(random_numbers)

        i = 0
        for edge in v.in_edges():
            g.ep.weight[edge] = random_numbers[i]
            i += 1


model = LTM(g, LTM_Agent, base.Connection)
model.set_graph_viz(True,
                    geometry=(1500, 1000),
                    vertex_fill_color=g.vp.color)

model.set_plot_viz(True, method=model.number_active_nodes, x_low=0, x_high=100, y_low=0, y_high=1000)

# Seed selection
# model.agents.sort(key=lambda a: a.v.out_degree(), reverse=True)
for agent in model.agents[0:500]:
    agent = random.choice(model.agents)
    event = base.Event(model, base.EventType.AGENT_V, 'active', True, agent.v)
    model.timeline.add_event(0, event)

model.start()

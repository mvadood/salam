import base
from graph_util import price_network
import numpy as np

g = price_network(1000)
weight_prop = g.new_edge_property('object')
g.ep['weight'] = weight_prop
edge_width_prop = g.new_edge_property('float')
g.ep.width = edge_width_prop


class RandWeightModel(base.Model):
    def __init__(self, g, agent_class, connection_class):
        super().__init__(g, agent_class, connection_class)

    def select(self):
        return None, np.random.choice(self.connections, np.random.randint(len(self.connections)) + 1, replace=False)

    def connection_action(self, connection):
        new_val = self.g.ep['weight'][connection.e] + np.random.choice([-1, 1])
        event = base.Event(self, base.EventType.CONNECTION_E, 'weight', new_val, connection.e)
        self.timeline.add_event(self.now + np.random.randint(5) + 1, event)

    def should_stop(self):
        return self.now >= 10000

    def update_entity_viz(self, event_type, entity):
        if event_type == base.EventType.CONNECTION_E:
            self.g.ep.width[entity] = self.g.ep.weight[entity] / 5

    def average_edge_weight(self):
        weights = [self.g.ep.weight[c.e] for c in self.connections]
        return np.mean(weights)


class WeightedConnection(base.Connection):
    def __init__(self, e):
        super().__init__(e)
        g.ep.weight[self.e] = np.random.randint(10)


model = RandWeightModel(g, agent_class=base.Agent, connection_class=WeightedConnection)
model.set_graph_viz(True,
                    geometry=(1500, 1000),
                    edge_pen_width=g.ep.width)
model.set_plot_viz(True, method=model.average_edge_weight, x_low=0, x_high=100, y_low=2, y_high=6)
model.start()

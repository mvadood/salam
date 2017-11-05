import logging
from enum import Enum

import time
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from gi.overrides.Gtk import Gtk
from graph_tool.draw import GraphWindow
from graph_tool.draw import sfdp_layout
import matplotlib.pyplot as plt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EventType(Enum):
    AGENT = 1
    AGENT_V = 2
    CONNECTION = 3
    CONNECTION_E = 4
    MODEL = 5
    MODEL_GRAPH = 6


class Event:
    def __init__(self, model, event_type, prop_name, new_val, entity=None):
        self.model = model
        self.entity = entity
        self.event_type = event_type
        self.prop_name = prop_name
        self.new_val = new_val

    def perform(self):
        if self.event_type == EventType.AGENT or \
                        self.event_type == EventType.CONNECTION or \
                        self.event_type == EventType.MODEL:
            self.entity.__setattr__(self.prop_name, self.new_val)
        elif self.event_type == EventType.AGENT_V:
            self.model.g.vp[self.prop_name][self.entity] = self.new_val
        elif self.event_type == EventType.CONNECTION_E:
            self.model.g.ep[self.prop_name][self.entity] = self.new_val
        elif self.event_type == EventType.MODEL_GRAPH:
            self.model.g.gp[self.prop_name] = self.new_val
        if self.model.graph_viz:
            self.model.update_entity_viz(self.event_type, self.entity)


class Timeline:
    def __init__(self):
        self.timeline = {}

    def add_event(self, step_index, event):
        if step_index not in self.timeline:
            self.timeline[step_index] = [event]
        else:
            step_events = self.timeline[step_index]
            step_events.append(event)

    def execute_events(self, step_index):
        if step_index in self.timeline:
            step_events = self.timeline[step_index]
            logger.info('Executing {} registered events...'.format(len(step_events)))
            for event in step_events:
                event.perform()


class Agent:
    def __init__(self, v):
        self.v = v


class Connection:
    def __init__(self, e):
        self.e = e


class Model:
    def __init__(self,
                 g,
                 agent_class=Agent,
                 connection_class=Connection
                 ):
        self.agent_class = agent_class
        self.connection_class = connection_class
        self.g = g

        self.graph_viz = False
        self.graph_viz_params = {}
        self.plot_viz = False
        self.plot_viz_params = {}
        self.plot_method_name = None
        self.plot = None

        self.agents = [agent_class(v) for v in g.vertices()]
        self.connections = [connection_class(e) for e in g.edges()]

        self.now = 0
        self.timeline = Timeline()

    def set_graph_viz(self, enable, **kwargs):
        self.graph_viz = enable
        self.graph_viz_params = kwargs

    def set_plot_viz(self, enable, method, **kwargs):
        self.plot_viz = enable
        self.plot_viz_params = kwargs
        self.plot_method = method

    def init_graph_viz(self):
        pos = sfdp_layout(self.g)

        if 'pos' in self.graph_viz_params:
            pos = self.graph_viz_params['pos']
            self.graph_viz_params.__delitem__('pos')

        self.win = GraphWindow(self.g, pos, **self.graph_viz_params)
        self.win.connect("delete_event", Gtk.main_quit)
        GObject.idle_add(self.simulate)
        self.win.show_all()

    # TODO: Use the animation package
    # TODO: Make it possible to draw multiple plots
    # TODO: Use should be able to assign labels, names, etc
    def init_plot_viz(self):
        self.xdata = []  # TODO: avoid such self assignments
        self.ydata = []
        plt.show()

        x_low = 0
        x_high = 100
        y_low = 0
        y_high = 100

        if 'x_low' in self.plot_viz_params:
            x_low = self.plot_viz_params['x_low']
        if 'x_high' in self.plot_viz_params:
            x_high = self.plot_viz_params['x_high']
        if 'y_low' in self.plot_viz_params:
            y_low = self.plot_viz_params['y_low']
        if 'y_high' in self.plot_viz_params:
            y_high = self.plot_viz_params['y_high']

        axes = plt.gca()
        axes.set_xlim(x_low, x_high)
        axes.set_ylim(y_low, y_high)
        self.line, = axes.plot(self.xdata, self.ydata, 'r-')

    def update_graph_viz(self):
        self.win.graph.regenerate_surface()
        self.win.graph.queue_draw()

    def update_entity_viz(self, event_type, entity):
        """You should override this method to achieve your desired visualization"""
        pass

    def should_stop(self):
        """Override this method if you need to"""
        return False

    def simulate(self):
        logger.info('+++++++++++++++++++ Starting the simulation +++++++++++++++++++')
        if not self.graph_viz:  # We should implement the loop ourselves
            while not self.should_stop():
                self.simulation_action()
        else:  # Looping is done via Gtk
            self.simulation_action()
            return not self.should_stop()

    def select(self):
        """"You should override this method, but keep the format of the output as it is now"""
        return self.agents, self.connections

    def agent_action(self, agent):
        """Override these method. You should generate agent_related events and push them into the timeline"""
        pass

    def connection_action(self, connection):
        """Override these method. You should generate connection_related events and push them into the timeline"""
        pass

    def model_action(self):
        """Override these method. You should generate model_related events and push them into the timeline"""
        pass

    def update_plot(self):
        self.xdata.append(self.now)
        self.ydata.append(self.plot_method())
        self.line.set_xdata(self.xdata)
        self.line.set_ydata(self.ydata)
        plt.draw()
        plt.pause(1e-17)  # TODO: make it a parameter somewhere

    def simulation_action(self):
        logger.info('---------------- Simulating step {} ----------------'.format(self.now))
        self.timeline.execute_events(self.now)

        if self.plot_viz:
            self.update_plot()

        logger.info('Generating new events...')
        selected_agents, selected_cons = self.select()
        if selected_agents is not None:
            for agent in selected_agents:
                self.agent_action(agent)

        if selected_cons is not None:
            for con in selected_cons:
                self.connection_action(con)

        self.model_action()

        logger.info('Event generation was done')
        if self.graph_viz:
            self.update_graph_viz()
        self.now += 1
        time.sleep(0.5)  # TODO: make it a parameter

    def start(self):
        if self.plot_viz:
            self.init_plot_viz()
        if not self.graph_viz:
            self.simulate()
        else:
            self.init_graph_viz()
            Gtk.main()

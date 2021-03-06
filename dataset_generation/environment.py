import random
import logging
import networkx as nx


class Environment(object):
    """
        Class containing the environment definition.
        The environment is a graph where each node has some attributes.
        Most nodes have sensors, which norm enforcers use to detect violations.
        Three different agents act over the environment:
        1. Cars: Drive through the graph nodes.
        2. Norm Enforcers: Cover some sensors in to capture violations.
        3. Observers: Spread over the graph, they perceive when violations
            occur or not. 
    """
    def __init__(self, G, node_prob, cars, obs, enfs, max_tr_li=2,
        max_speed=10):
        self.graph = G
        self.node_prob = node_prob
        self.cars = cars
        self.obs = obs
        self.enfs = enfs
        self.max_tr_li = max_tr_li
        self.max_speed = max_speed
        
    def modify(self):
        """
            Check all nodes and modify them using a probability.
        """        
        for n in self.graph.nodes:

            if 'signal' in self.graph.node[n]:
                # If node has a signal, try to change it to red or
                # green.
                if random.random() <= self.node_prob:
                    cur_signal = self.graph.node[n]['signal']
                    new_signal = (cur_signal * (-1)) + 1
                    logging.debug(
                        "Traffic light changed from %d to %d in node %d." % (
                            cur_signal, new_signal, n))
                    self.graph.node[n]['signal'] = new_signal

            elif 'prohibition' in self.graph.node[n]:
                # If node has a prohibition status, try to modify it.
                if random.random() <= self.node_prob:
                    cur_status = self.graph.node[n]['prohibition']
                    new_status = (cur_status * (-1)) + 1
                    logging.debug(
                        "Prohibition changed from %d to %d in node %d." % (
                            cur_status, new_status, n))
                    self.graph.node[n]['prohibition'] = new_status                    

    def move_car(self, car, next_node):

        logging.debug("Car %d in %d moving to node %d" % (car.id, car.cur_pos, 
            next_node))

        if car.cur_pos == next_node:
            logging.debug("Car kept in the same place: %d" % next_node)
            car.visited.append(next_node)
            return next_node

        cur_pos = car.cur_pos
        g = self.graph
        node_prob = g[cur_pos][next_node]["weight"]
        rand_prob = random.random()
        logging.debug("Next node ({}) prob: {}".format(next_node, node_prob))
        logging.debug("Random prob: {}".format(rand_prob))
        car_in_node = None
        if "car" not in g.node[next_node]:
            # Ensure that there is a key for car in node.
            g.node[next_node]["car"] = []
        elif g.node[next_node]["car"]:
            car_in_node = g.node[next_node]["car"][0]
        if rand_prob <= node_prob and not car_in_node:
            car.prev_pos = car.cur_pos
            car.cur_pos = next_node
            car.visited.append(next_node)
            self.update_car_position(car)
            logging.debug("Car %d moved to node %d" % (car.id,
                        next_node))
        else:
            # Go to neighbours.
            neighbours = g.neighbors(car.cur_pos)
            for neig in neighbours:
                car_in_node = None
                if neig == next_node:
                    # Car must not try the same node twice.
                    continue
                    
                new_prob = g[car.cur_pos][neig]['weight']
                node_prob += new_prob
                rand_prob = random.random()
                logging.debug("Car {} trying to go to {} with prob {} and rand_prob {}".format(
                    car.id, neig, node_prob, rand_prob))
                if "car" not in g.node[neig]:
                    g.node[neig]["car"] = []
                elif g.node[neig]["car"]:
                    car_in_node = g.node[neig]["car"][0]
                logging.debug("Car in node: {}".format(car_in_node))
                logging.debug("Condition to go to neighbour: {} and ({} or {})".format(rand_prob <= node_prob, car_in_node == None, car_in_node == car.id))
                if rand_prob <= node_prob and (car_in_node == None or
                    car_in_node == car.id):
                    car.modify_speed(self, g, neig)
                    car.prev_pos = car.cur_pos
                    car.cur_pos = neig
                    car.visited.append(neig)
                    self.update_car_position(car)
                    logging.debug("Car %d moved to node %d" % (car.id,
                        neig))
                    return neig
            logging.debug("Can't move cause no node was available.")

    def update_car_position(self, car):
        """
            Change the current position for car.
        """
        car_id = car.id
        prev_pos = car.prev_pos
        cur_pos = car.cur_pos
        index = self.graph.node[prev_pos]['car'].index(car_id)
        self.graph.node[prev_pos]['car'].pop(index)
        if 'car' in self.graph.node[cur_pos]:
            self.graph.node[cur_pos]['car'].append(car_id)
        else:
            self.graph.node[cur_pos]['car'] = [car_id]

    def check_cars(self):
        """
            Remove cars from environment if they are in the goal node.
        """
        remove_list = []

        for car_id in self.cars:
            car = self.cars[car_id]
            if car.cur_pos == car.goal:
                logging.debug(
                    "Removing car %d from environment. It reached goal %d" % (
                        car_id, car.goal))
                index = self.graph.node[car.cur_pos]['car'].index(car_id)
                self.graph.node[car.cur_pos]['car'].pop(index)

                if car_id in self.cars:
                    remove_list.append(car_id)
                    
        for car_id in remove_list:
            del self.cars[car_id]
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from mesa import Model, DataCollector
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from agents.donor import Donor
from agents.recipient import Recipient
from agents.transport import Transport
import numpy as np
from deap import base, creator, tools, algorithms
import acopy
from pyswarm import pso
# DEAP setup outside class to avoid redefinition warnings
if not hasattr(creator, "FitnessMulti"):
    creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMulti)

# DEAP setup outside class to avoid redefinition warnings
if not hasattr(creator, "FitnessMulti"):
    creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMulti)

class FoodRedistributionModel(Model):
    def __init__(self, num_donors=30, num_recipients=10, num_transports=5):
        super().__init__()
        self.step_count = 0
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(10, 10, True)
        self.food_queue = []
        self.missed_deliveries = 0
        self.queue_times = []
        self.num_transports = num_transports
        self.datacollector = DataCollector(
            model_reporters={"Queue Length": lambda m: len(m.food_queue)}
        )

        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self._generate_indices)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self._evaluate_route)
        self.toolbox.register("mate", tools.cxPartialyMatched)
        self.toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

        for i in range(num_donors):
            donor = Donor(i, self)
            self.schedule.add(donor)
            self.grid.place_agent(donor, (i % 10, i // 10))
        for i in range(num_recipients):
            recipient = Recipient(i + num_donors, self)
            self.schedule.add(recipient)
            self.grid.place_agent(recipient, (5 + (i % 5), i // 5))
        for i in range(num_transports):
            transport = Transport(i + num_donors + num_recipients, self)
            self.schedule.add(transport)
            self.grid.place_agent(transport, (9, i))

    def _generate_indices(self):
        all_pairs = [(d.unique_id, r.unique_id)
                     for d in self.schedule.agents if isinstance(d, Donor)
                     for r in self.schedule.agents if isinstance(r, Recipient)]
        if not all_pairs:
            return []
        k = min(len(self.food_queue), len(all_pairs), self.num_transports * 2)
        k = max(1, k)
        k = min(k, len(all_pairs))
        print(f"DEBUG: _generate_indices - all_pairs: {len(all_pairs)}, k: {k}")
        return list(range(k))

    def _evaluate_route(self, individual):
        if not individual:
            return 1000, 1000, 1000
        total_distance = 0
        loads = [0] * self.num_transports
        total_urgency = 0
        all_pairs = [(d.unique_id, r.unique_id)
                     for d in self.schedule.agents if isinstance(d, Donor)
                     for r in self.schedule.agents if isinstance(r, Recipient)]
        if not all_pairs:
            return 1000, 1000, 1000
        assigned_donors = set()
        for i, idx in enumerate(individual):
            idx = idx % len(all_pairs)
            donor_id, recipient_id = all_pairs[idx]
            if donor_id in assigned_donors:
                continue
            assigned_donors.add(donor_id)
            donor = next(a for a in self.schedule.agents if a.unique_id == donor_id)
            recipient = next(a for a in self.schedule.agents if a.unique_id == recipient_id)
            distance = abs(donor.pos[0] - recipient.pos[0]) + abs(donor.pos[1] - recipient.pos[1])
            total_distance += distance
            loads[i % self.num_transports] += 1
            for item in self.food_queue:
                if len(item) == 4:
                    q_donor_id, _, timer, food_type = item
                else:
                    q_donor_id, _, timer, food_type, _ = item
                if q_donor_id == donor_id and food_type == "perishable":
                    total_urgency += max(0, 1000 - timer)
        load_imbalance = np.var(loads)
        return total_distance, load_imbalance, total_urgency

    def greedy_routes(self):
        available_transports = [a for a in self.schedule.agents if isinstance(a, Transport) and not a.route]
        if not self.food_queue or not available_transports:
            return
        assigned_donors = set()
        for i, item in enumerate(self.food_queue[:]):
            if len(item) == 4:
                donor_id, _, _, _ = item
            else:
                donor_id, _, _, _, _ = item
            if donor_id in assigned_donors:
                continue
            donkey = next(a for a in self.schedule.agents if a.unique_id == donor_id)
            recipient = min(
                [a for a in self.schedule.agents if isinstance(a, Recipient)],
                key=lambda r: abs(r.pos[0] - donkey.pos[0]) + abs(r.pos[1] - donkey.pos[1]),
                default=None
            )
            if recipient and available_transports:
                transport = available_transports.pop(0)
                transport.route.append((donor_id, recipient.unique_id))
                assigned_donors.add(donor_id)
                print(f"DEBUG: greedy_routes - Assigned {donor_id} to {recipient.unique_id} for transport {transport.unique_id}")

    def ant_colony_optimization(self):
        available_transports = [a for a in self.schedule.agents if isinstance(a, Transport) and not a.route]
        if not self.food_queue or not available_transports:
            return

        # Create a graph for ACO based on agent positions
        graph = acopy.Graph()
        nodes = []
        donor_positions = {}
        recipient_positions = {}
        for agent in self.schedule.agents:
            if isinstance(agent, Donor) or isinstance(agent, Recipient):
                node = f"{agent.unique_id}_{agent.pos[0]}_{agent.pos[1]}"
                nodes.append(node)
                if isinstance(agent, Donor):
                    donor_positions[agent.unique_id] = node
                else:
                    recipient_positions[agent.unique_id] = node
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                x1, y1 = map(int, node1.split('_')[1:3])
                x2, y2 = map(int, node2.split('_')[1:3])
                distance = abs(x1 - x2) + abs(y1 - y2) or 1  # Ensure non-zero distance
                graph.add_edge(node1, node2, distance)

        solver = acopy.Solver(rho=0.1, q=1.0)
        colony = acopy.Colony(alpha=1.0, beta=2.0)
        assigned_donors = set()
        for i, item in enumerate(self.food_queue[:]):
            if len(item) == 4:
                donor_id, _, _, _ = item
            else:
                donor_id, _, _, _, _ = item
            if donor_id in assigned_donors or not available_transports:
                continue
            donor_node = donor_positions.get(donor_id)
            if not donor_node:
                continue
            # Find closest recipient
            recipient = min(
                [a for a in self.schedule.agents if isinstance(a, Recipient)],
                key=lambda r: abs(r.pos[0] - self.schedule.agents[donor_id].pos[0]) + 
                             abs(r.pos[1] - self.schedule.agents[donor_id].pos[1]),
                default=None
            )
            if not recipient:
                continue
            recipient_node = recipient_positions.get(recipient.unique_id)
            # Run ACO to find path
            try:
                tour = solver.solve(graph, colony, start=donor_node, end=recipient_node, limit=50)
                if tour and tour.nodes:
                    transport = available_transports.pop(0)
                    transport.route.append((donor_id, recipient.unique_id))
                    assigned_donors.add(donor_id)
                    print(f"DEBUG: ACO - Assigned {donor_id} to {recipient.unique_id} for transport {transport.unique_id}")
            except Exception as e:
                print(f"ACO failed: {e}")
                continue
        solver.stop()

    def particle_swarm_optimization(self):
        available_transports = [a for a in self.schedule.agents if isinstance(a, Transport) and not a.route]
        if not self.food_queue or not available_transports:
            return

        # PSO to prioritize donations
        def objective(weights):
            total_urgency = 0
            total_distance = 0
            for i, item in enumerate(self.food_queue[:len(weights)]):
                if len(item) == 4:
                    donor_id, _, timer, food_type = item
                else:
                    donor_id, _, timer, food_type, _ = item
                donor = next(a for a in self.schedule.agents if a.unique_id == donor_id)
                recipient = min(
                    [a for a in self.schedule.agents if isinstance(a, Recipient)],
                    key=lambda r: abs(r.pos[0] - donor.pos[0]) + abs(r.pos[1] - donor.pos[1]),
                    default=None
                )
                if not recipient:
                    continue
                distance = abs(donor.pos[0] - recipient.pos[0]) + abs(donor.pos[1] - recipient.pos[1])
                urgency = (1000 - timer) if food_type == "perishable" else 0
                total_urgency += weights[i] * urgency
                total_distance += weights[i] * distance
            return total_urgency + total_distance

        lb = [0] * len(self.food_queue)
        ub = [1] * len(self.food_queue)
        try:
            xopt, _ = pso(objective, lb, ub, swarmsize=20, maxiter=30)
        except Exception as e:
            print(f"PSO failed: {e}")
            self.greedy_routes()
            return

        # Assign routes based on PSO weights
        sorted_indices = np.argsort(xopt)[::-1]  # Highest weights first
        assigned_donors = set()
        for idx in sorted_indices:
            if not available_transports:
                break
            if len(self.food_queue[idx]) == 4:
                donor_id, _, _, _ = self.food_queue[idx]
            else:
                donor_id, _, _, _, _ = self.food_queue[idx]
            if donor_id in assigned_donors:
                continue
            donor = next(a for a in self.schedule.agents if a.unique_id == donor_id)
            recipient = min(
                [a for a in self.schedule.agents if isinstance(a, Recipient)],
                key=lambda r: abs(r.pos[0] - donor.pos[0]) + abs(r.pos[1] - donor.pos[1]),
                default=None
            )
            if recipient:
                transport = available_transports.pop(0)
                transport.route.append((donor_id, recipient.unique_id))
                assigned_donors.add(donor_id)
                print(f"DEBUG: PSO - Assigned {donor_id} to {recipient.unique_id} for transport {transport.unique_id}")

    def optimize_routes(self):
        if len(self.food_queue) < 1 or len(self.schedule.agents) < 2:
            self.greedy_routes()
            return

        all_pairs = [(d.unique_id, r.unique_id)
                     for d in self.schedule.agents if isinstance(d, Donor)
                     for r in self.schedule.agents if isinstance(r, Recipient)]
        if not all_pairs:
            self.greedy_routes()
            return

        k = min(len(self.food_queue), len(all_pairs), self.num_transports * 2)
        k = max(1, k)
        k = min(k, len(all_pairs))
        if k == 1:
            print("DEBUG: optimize_routes - Skipping metaheuristics for k=1, using greedy_routes")
            self.greedy_routes()
            return

        available_transports = [a for a in self.schedule.agents if isinstance(a, Transport) and not a.route]
        if len(available_transports) < min(k, self.num_transports):
            print("DEBUG: optimize_routes - Not enough available transports, using greedy_routes")
            self.greedy_routes()
            return

        if k <= 5:
            pop_size = min(20, len(all_pairs))
            pop = self.toolbox.population(n=pop_size)
            try:
                for ind in pop:
                    if not ind:
                        ind[:] = [0] * min(len(all_pairs), self.num_transports * 2)
                    for i in range(len(ind)):
                        ind[i] = ind[i] % len(all_pairs) if all_pairs else 0
                algorithms.eaSimple(pop, self.toolbox, cxpb=0.7, mutpb=0.2, ngen=30, verbose=False)
            except Exception as e:
                print(f"GA optimization failed: {e}")
                self.greedy_routes()
                return

            best_individual = tools.selBest(pop, k=1)[0]
            routes_assigned = False
            assigned_donors = set()
            for i, idx in enumerate(best_individual):
                idx = idx % len(all_pairs) if all_pairs else 0
                donor_id, recipient_id = all_pairs[idx]
                if donor_id in assigned_donors:
                    continue
                assigned_donors.add(donor_id)
                try:
                    transport = available_transports[i % len(available_transports)]
                    transport.route.append((donor_id, recipient_id))
                    routes_assigned = True
                    print(f"DEBUG: optimize_routes - Assigned {donor_id} to {recipient_id} for transport {transport.unique_id}")
                except IndexError:
                    continue
            if not routes_assigned:
                print("DEBUG: optimize_routes - No routes assigned by GA, using greedy_routes")
                self.greedy_routes()

        elif k <= 10:
            self.ant_colony_optimization()
        else:
            self.particle_swarm_optimization()

    def step(self):
        self.step_count += 1
        new_queue = []
        for item in self.food_queue:
            if len(item) == 4:
                donor_id, amount, timer, food_type = item
                start_step = self.step_count
            else:
                donor_id, amount, timer, food_type, start_step = item
            if timer > 0:
                new_queue.append((donor_id, amount, timer - 1, food_type, start_step))
            elif food_type == "perishable":
                self.missed_deliveries += 1
        self.food_queue = new_queue
        print(f"DEBUG: Food Queue: {self.food_queue}")
        self.schedule.step()
        self.optimize_routes()
        self.datacollector.collect(self)

if __name__ == "__main__":
    model = FoodRedistributionModel(num_donors=2, num_recipients=2, num_transports=2)
    for i in range(25):
        model.step()
        print(f"Step {i}: Queue Length = {len(model.food_queue)}, Missed Deliveries = {model.missed_deliveries}")
    print(f"Final Results: Missed Deliveries = {model.missed_deliveries}, "
          f"Avg Queue Time = {np.mean(model.queue_times) if model.queue_times else 0}")
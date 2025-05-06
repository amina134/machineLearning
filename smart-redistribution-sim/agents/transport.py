from mesa import Agent
import random

class Transport(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.capacity = 30  # Max food units carryable
        self.carried_food = 0  # Current load
        self.speed = 1  # Cells per step

    def step(self):
        # 1. Collect food from donors if empty
        if self.carried_food == 0:
            self._collect_food()
        
        # 2. Move toward recipients with demand
        self._move()
        
        # 3. Deliver food when near recipients
        self._deliver()

    def _collect_food(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cellmates:
            if isinstance(agent, Donor) and agent.food_amount > 0:
                collectable = min(
                    agent.food_amount,
                    self.capacity - self.carried_food
                )
                agent.food_amount -= collectable
                self.carried_food += collectable
                print(f"Transport {self.unique_id} collected {collectable} units")

    def _move(self):
        if self.carried_food > 0:  # Only move if carrying food
            possible_steps = self.model.grid.get_neighborhood(
                self.pos,
                moore=True,  # Allows diagonal movement
                include_center=False
            )
            new_position = random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def _deliver(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cellmates:
            if isinstance(agent, Recipient):
                # Delivery handled in Recipient.step()
                pass
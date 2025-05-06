from mesa import Agent

class Recipient(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.demand = 50  # Total food units needed
        self.received = 0  # Track received donations
        self.storage_capacity = 100  # Max food that can be stored

    def step(self):
        # Check if still needs food
        if self.received < self.demand:
            # Get all agents at current position
            cellmates = self.model.grid.get_cell_list_contents([self.pos])
            
            # Look for Transport agents carrying food
            for agent in cellmates:
                if isinstance(agent, Transport) and agent.carried_food > 0:
                    # Take as much as needed/available
                    transfer = min(
                        agent.carried_food, 
                        self.demand - self.received,
                        self.storage_capacity - self.received
                    )
                    agent.carried_food -= transfer
                    self.received += transfer
                    print(f"Recipient {self.unique_id} received {transfer} units (Total: {self.received}/{self.demand})")
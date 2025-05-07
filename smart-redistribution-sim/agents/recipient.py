from mesa import Agent

class Recipient(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.demand = 50
        self.received = 0
        self.storage_capacity = 100

    def receive_food(self, amount):
        transfer = min(amount, self.demand - self.received, self.storage_capacity - self.received)
        self.received += transfer
        print(f"Recipient {self.unique_id} received {transfer} units (Total: {self.received}/{self.demand})")
        return transfer

    def step(self):
        pass
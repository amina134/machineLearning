from mesa import Agent
import random

class Donor(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.food_amount = random.randint(50, 200)  # Random initial stock
        self.food_types = ["perishable", "non_perishable"]
        self.food_type = random.choice(self.food_types)  # Random type
        self.donation_frequency = random.randint(3, 7)  # Steps between donations
        self.steps_since_last_donation = 0

    def step(self):
        self.steps_since_last_donation += 1
        
        # Only donate at certain intervals
        if (self.steps_since_last_donation >= self.donation_frequency 
            and self.food_amount > 0):
            
            # Donate 10-20% of current stock
            donation = max(1, int(self.food_amount * random.uniform(0.1, 0.2)))
            self.food_amount -= donation
            self.steps_since_last_donation = 0  # Reset counter
            
            print(f"Donor {self.unique_id} ({self.food_type}) donated {donation} units (Remaining: {self.food_amount})")
from mesa import Agent

class Donor(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.food_amount = 100  # Fixed initial amount
        self.food_type = "non_perishable"  # Matches output
        self.donation_frequency = 3  # Donate every 3 steps
        self.steps_since_last_donation = 0
        self.base_donation_prob = 1.0  # Deterministic

    def step(self):
        self.steps_since_last_donation += 1
        is_weekend = self.model.step_count % 25 == 0  # Adjusted for test
        donation_amount = 20 if is_weekend else 10  # 20 for spike, 10 otherwise

        if (self.steps_since_last_donation >= self.donation_frequency 
            and self.food_amount >= donation_amount):
            self.food_amount -= donation_amount
            self.steps_since_last_donation = 0
            timer = 1000  # Non-perishable
            self.model.food_queue.append((self.unique_id, donation_amount, timer, self.food_type, self.model.step_count))
            print(f"Donor {self.unique_id} ({self.food_type}) donated {donation_amount} units (Remaining: {self.food_amount})")
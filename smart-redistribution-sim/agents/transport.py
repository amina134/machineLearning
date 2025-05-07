from mesa import Agent

class Transport(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.capacity = 30
        self.carried_food = 0
        self.speed = 1
        self.route = []
        self.current_donation_start_step = None

    def step(self):
        print(f"DEBUG: Transport {self.unique_id} - Route: {self.route}, Carried Food: {self.carried_food}")
        if self.carried_food == 0 and self.route:
            self._collect_food()
        elif self.carried_food > 0 and self.route:
            self._deliver()
        else:
            self.route = []  # Clear route if no action is taken

    def _collect_food(self):
        if not self.route:
            return
        donor_id, _ = self.route[0]
        donor = next((a for a in self.model.schedule.agents if a.unique_id == donor_id), None)
        if not donor:
            self.route.pop(0)
            return
        self.model.grid.move_agent(self, donor.pos)
        for i, item in enumerate(self.model.food_queue[:]):
            if len(item) == 4:
                q_donor_id, amount, timer, food_type = item
                start_step = self.model.step_count
            else:
                q_donor_id, amount, timer, food_type, start_step = item
            if q_donor_id == donor_id and self.carried_food < self.capacity:
                collectable = min(amount, self.capacity - self.carried_food)
                self.carried_food += collectable
                self.current_donation_start_step = start_step
                self.model.food_queue[i] = (q_donor_id, amount - collectable, timer, food_type, start_step)
                if amount - collectable <= 0:
                    self.model.food_queue.pop(i)
                print(f"Transport {self.unique_id} collected {collectable} units from Donor {donor_id}")
                break
        if self.carried_food == 0:  # If no food was collected, clear the route
            self.route.pop(0)

    def _deliver(self):
        if not self.route:
            return
        _, recipient_id = self.route[0]
        recipient = next((a for a in self.model.schedule.agents if a.unique_id == recipient_id), None)
        if not recipient:
            self.route.pop(0)
            return
        self.model.grid.move_agent(self, recipient.pos)
        if self.carried_food > 0:
            transferred = recipient.receive_food(self.carried_food)
            self.carried_food -= transferred
            if transferred > 0 and self.current_donation_start_step is not None:
                queue_time = self.model.step_count - self.current_donation_start_step
                self.model.queue_times.append(queue_time)
            print(f"Transport {self.unique_id} delivered {transferred} units to Recipient {recipient_id}")
            self.route.pop(0)
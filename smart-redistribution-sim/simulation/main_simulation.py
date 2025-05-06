import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))


from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agents.donor import Donor
from agents.recipient import Recipient
from agents.transport import Transport

class FoodRedistributionModel(Model):
    def __init__(self, num_donors=5, num_recipients=3, num_transports=2):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(10, 10, True)
        
        # Create agents
    # donor
        for i in range(num_donors):
            donor = Donor(i, self)
            self.schedule.add(donor)
            self.grid.place_agent(donor, self._random_pos())
        
        # Similar for recipients and transports...
    # recipient
        for i in range(num_recipients):
            recipient=Recipient(i+num_donors,self)
            self.schedule.add(recipient)
            self.grid.place_agent(recipient, self._random_pos())
     # transporter
        for i in range(num_transports):
            transport=Transport(i+num_donors +num_recipients,self)
            self.schedule.add(transport)
            self.grid.place_agent(transport, self._random_pos())
        


    
    def _random_pos(self):
        return (self.random.randrange(10), self.random.randrange(10))
    
    def step(self):
        self.schedule.step()
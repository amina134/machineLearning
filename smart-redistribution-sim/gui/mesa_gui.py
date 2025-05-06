
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))


from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from simulation.main_simulation import FoodRedistributionModel
# ADD THESE IMPORTS
from agents.donor import Donor
from agents.recipient import Recipient
from agents.transport import Transport

def agent_portrayal(agent):
    # Base portrayal properties (MUST include Layer)
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "r": 0.5,
        "Layer": 0,  # Default layer
        "text": str(agent.unique_id),  # Optional: show agent IDs
        "text_color": "white"
    }

    # Type-specific customizations
    if isinstance(agent, Donor):
        portrayal.update({
            "Color": "green",
            "Layer": 0,
            "text": f"D{agent.unique_id}"  # D for donor
        })
    elif isinstance(agent, Recipient):
        portrayal.update({
            "Color": "red",
            "Layer": 1,
            "text": f"R{agent.unique_id}"  # R for recipient
        })
    elif isinstance(agent, Transport):
        portrayal.update({
            "Color": "blue",
            "Layer": 2,
            "text": f"T{agent.unique_id}"  # T for transport
        })
    
    return portrayal
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
server = ModularServer(FoodRedistributionModel, [grid], "Food Redistribution")
server.launch()
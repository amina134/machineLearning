import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from simulation.main_simulation import FoodRedistributionModel
from agents.donor import Donor
from agents.recipient import Recipient
from agents.transport import Transport

def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "r": 0.5,
        "Layer": 0,
        "text": str(agent.unique_id),
        "text_color": "white"
    }
    if isinstance(agent, Donor):
        portrayal.update({
            "Color": "green",
            "Layer": 0,
            "text": f"D{agent.unique_id}"
        })
    elif isinstance(agent, Recipient):
        portrayal.update({
            "Color": "red",
            "Layer": 1,
            "text": f"R{agent.unique_id}"
        })
    elif isinstance(agent, Transport):
        portrayal.update({
            "Color": "blue",
            "Layer": 2,
            "text": f"T{agent.unique_id}"
        })
    return portrayal

grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

server = ModularServer(
    FoodRedistributionModel,
    [grid],
    "Food Redistribution",
    {"num_donors": 2, "num_recipients": 2, "num_transports": 2}
)
server.port = 8521
server.launch()
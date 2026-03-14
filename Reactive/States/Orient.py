from StateMachine.State import State 
from States.AgentConsts import AgentConsts


class Orient(State) : 
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        #De momento no hace nada 

        self.directionToLook = agent.direction
        print("Orientadose...\n")
        return self.directionToLook, False 
    
    def Transit(self,perception, map):
        return "Shoot"
    
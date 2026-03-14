
from StateMachine.State import State 
from States.AgentConsts import AgentConsts


class RunAway (State) : 
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        #Buscar huecos en las direcciones contrarias a las balas 
            #Ir hacia alli durante un tiempo
     
        self.action = self.safePlace(perception, agent)
        return self.action, False
    
    def Transit(self,perception, map):
        return "Detect"

    def safePlace(self, perception, agent) : 

        if agent.direction in [AgentConsts.NEIGHBORHOOD_UP, AgentConsts.NEIGHBORHOOD_DOWN] : 
            if self.canGo(perception[AgentConsts.NEIGHBORHOOD_LEFT],perception[AgentConsts.NEIGHBORHOOD_DIST_LEFT] ): 
                return AgentConsts.MOVE_LEFT
            elif self.canGo(perception[AgentConsts.NEIGHBORHOOD_RIGHT], perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT]): 
                return AgentConsts.MOVE_RIGHT
            
        if agent.direction in [AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.NEIGHBORHOOD_LEFT] : 
            if self.canGo(perception[AgentConsts.NEIGHBORHOOD_UP], perception[AgentConsts.NEIGHBORHOOD_DIST_UP]) : 
                return AgentConsts.MOVE_UP
            elif self.canGo(perception[AgentConsts.NEIGHBORHOOD_DOWN], perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN]): 
                return AgentConsts.MOVE_DOWN 
        
        #Rendirse 
        print("Me rindo...")
        return AgentConsts.NO_MOVE 


    def canGo(self, object, distance) : 
        return (object == AgentConsts.NOTHING) 
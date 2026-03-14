
from StateMachine.State import State 
from States.AgentConsts import AgentConsts


class Detect (State) : 
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        #De momento no hace nada 
        print("Modo deteccion...\n")
        
        agent.direction,self.detection= self.findTarget(perception)

        return 0, False 
    
    def Transit(self,perception, map):

        if self.detection : 
            return "Orient"

        return self.id
    
    def findTarget(self, perception) :

        #Hay algo arriba 
        if perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.SHELL, AgentConsts.PLAYER ]: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_UP] <= 7 : 
                return 1, True 
            
        #Hay algo abajo 
        if perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.SHELL, AgentConsts.PLAYER ]: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN] <= 7 : 
                return 2, True 
            
        #Hay algo a la derecha  
        if perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.SHELL, AgentConsts.PLAYER ]: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT] <= 7 : 
                return 3, True 

        #Hay algo a la izquierda      
        if perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.SHELL, AgentConsts.PLAYER ]: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_LEFT] <= 7 : 
                return 4, True 
        
        return 0, False 
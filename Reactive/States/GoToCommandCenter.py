from StateMachine.State import State
from States.AgentConsts import AgentConsts
import random


class GoToCommandCenter(State):

    def __init__(self, id):
        super().__init__(id)
        self.Reset()

    def Update(self, perception, map, agent):
        self.updateTime += perception[AgentConsts.TIME]
        if self.updateTime > 1.0:
            self.Reset()
        return self.action,True
    
    def Transit(self,perception, map):
        return self.id
    
    def Reset(self):
        self.action = random.randint(1,4)
        self.updateTime = 0
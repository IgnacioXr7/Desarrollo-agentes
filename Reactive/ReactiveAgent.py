from Agent.BaseAgent import BaseAgent
from StateMachine.StateMachine import StateMachine
from States.AgentConsts import AgentConsts
from States.Shoot import Shoot 
from States.Detect import Detect
from States.Orient import Orient
from States.RunAway import RunAway
from States.AttackTarget import AttackTarget
from States.Escape import Escape
from States.GoToExit import GoToExit
from States.ShootAndOrient import ShootAndOrient
from Reactive.States.GoToCC import GoToCC



class ReactiveAgent(BaseAgent):
    def __init__(self, id, name):
        super().__init__(id, name)

        self.direction = AgentConsts.NEIGHBORHOOD_UP

        dictionary = {
            "GoToCC": GoToCC("GoToCC"),
            "AttackTarget": AttackTarget("AttackTarget"),
            #"Escape": Escape("Escape"),
            "GoToExit": GoToExit("GoToExit"),
            #"ShootAndOrient": ShootAndOrient("ShootAndOrient"),
            #"RunAway": RunAway("RunAway"),
            "Shoot": Shoot("Shoot"),
            "Orient": Orient("Orient"),
            #"Detect": Detect("Detect")
        }

        self.stateMachine = StateMachine("ReactiveBehavior", dictionary, "GoToCC")

    def Start(self):
        print("Inicio del agente ")
        self.stateMachine.Start(self)

    def Update(self, perception, map):
        action, shot = self.stateMachine.Update(perception, map, self)
        return action, shot
    
    def End(self, win):
        super().End(win)
        self.stateMachine.End()

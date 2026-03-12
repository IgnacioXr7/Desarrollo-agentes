from Agent.BaseAgent import BaseAgent
from StateMachine.GoToCommandCenter import GoToCommandCenter
from StateMachine.StateMachine import StateMachine


class ReactiveAgent(BaseAgent):
    def __init__(self, id, name):
        super().__init__(id, name)
        # Máquina de estados jerárquica
        dictionary = {
            "AttackTarget": AttackTarget("AttackTarget"),
            "Escape": Escape("Escape"),
            "GoToExit": GoToExit("GoToExit"),
            "ShootAndOrient": ShootAndOrient("ShootAndOrient")
        }
        # Estado inicial: Atacar
        self.stateMachine = StateMachine("ReactiveBehavior", dictionary, "AttackTarget")

    #Metodo que se llama al iniciar el agente. No devuelve nada y sirve para contruir el agente
    def Start(self):
        print("Inicio del agente ")
        self.stateMachine.Start(self)

    #Metodo que se llama en cada actualización del agente, y se proporciona le vector de percepciones
    #Devuelve la acción u el disparo si o no
    def Update(self, perception, map):
        action, shot = self.stateMachine.Update(perception, map, self)
        return action, shot
    
    #Metodo que se llama al finalizar el agente, se pasa el estado de terminacion
    def End(self, win):
        super().End(win)
        self.stateMachine.End()
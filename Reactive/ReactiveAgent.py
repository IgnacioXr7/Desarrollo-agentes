from Agent.BaseAgent import BaseAgent
from StateMachine.StateMachine import StateMachine
from States.GoToCommandCenter import GoToCommandCenter


class ReactiveAgent(BaseAgent):
    def __init__(self, id, name):
        super().__init__(id, name)
        dictionary = {
        "GoToCommandCenter" : GoToCommandCenter("GoToCommandCenter")
        }
        self.stateMachine = StateMachine("ReactiveBehavior",dictionary,"GoToCommandCenter")

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
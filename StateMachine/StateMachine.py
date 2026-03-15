from StateMachine.State import State

class StateMachine(State):
    def __init__(self, id, states, initial):
        super().__init__(id)
        self.states = states
        self.curentState = initial
    
    def Start(self, agent):
        print("Inicio de la maquina de estados")
        self.states[self.curentState].Start(agent)

    def Update(self, perception, map, agent):
        actions = self.states[self.curentState].Update(perception, map, agent)
        newState = self.states[self.curentState].Transit(perception, map)

        if newState != self.curentState:
            self.states[self.curentState].End()
            self.curentState = newState
            self.states[self.curentState].Start(agent)

        return actions

    def End(self, win = False):
        self.states[self.curentState].End()
        super().End()
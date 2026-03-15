from StateMachine.State import State
from States.AgentConsts import AgentConsts

class Shoot (State) : 
    def __init__(self, id):
        super().__init__(id)

    #Metodo que se llama al iniciar el estado
    def Start(self,agent):
        print("En estado disparar")

    #Metodo que se llama en cada actualización del estado
    #devuelve las acciones (actuadores) que el agente realiza
    def Update(self, perception, map, agent):
        #Dispara 
        print("Modo disparo")
        
        if self.searchBullet(perception) : #Si hay bala (lejos)
            if not perception[AgentConsts.CAN_FIRE] : #No puedo disparar aun 
                self.id= "RunAway"  #Huir 

        #Ya no hay objetivo 
        if perception[agent.direction] not in [AgentConsts.PLAYER, AgentConsts.SHELL] : 
            if perception[AgentConsts.PLAYER_X] == -1 or perception[AgentConsts.COMMAND_CENTER_X] == -1 : #El jugador esta muerto
                #Ir a por la estrella  
                self.id = "Detect"
            else : 
                #Esto sería ir a CC 
                self.id = "GoToCC"

        return agent.direction,True
    
    #método que se llama para decidir la transición del estado. Devuelve el id del estado nuevo
    def Transit(self,perception, map):
       
        return self.id #Sigo disparando 
    
    def searchBullet(self, perception) :

        #Hay algo arriba y es una bala  
        if perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.OTHER: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_UP] >= 4 : 
                return True 
            
        #Hay algo abajo y es una bala
        if perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.OTHER: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN] >= 4 : 
                return True 
            
        #Hay algo a la derecha y es una bala     
        if perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.OTHER: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT] >= 4 : 
                return True 

        #Hay algo a la izquierda y es una bala     
        if perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.OTHER: 
            if perception[AgentConsts.NEIGHBORHOOD_DIST_LEFT] >= 4 : 
                return True 
        
        return False 
from StateMachine.State import State
from States.AgentConsts import AgentConsts


class Escape(State):
    """
    Estado para huir de amenazas (balas enemigas).
    VERSIÓN FINAL ACTUALIZADA:
    - TIME está en índice 21 (no 20)
    - ORIENTATION en índice 20
    - Y INVERTIDA correctamente
    """

    def __init__(self, id):
        super().__init__(id)
        self.escape_time = 0
        self.max_escape_time = 2.0

    def Start(self, agent):
        print("=== INICIANDO ESTADO: ESCAPE ===")
        self.escape_time = 0

    def Update(self, perception, map, agent):
        """
        Se mueve en dirección opuesta a la bala más cercana.
        Y está invertida: UP opuesto a DOWN, DOWN opuesto a UP.
        TIME ahora está en índice 21.
        """
        if len(perception) < 10:
            return AgentConsts.NO_MOVE, False
        
        if len(perception) > AgentConsts.TIME:
            self.escape_time += perception[AgentConsts.TIME]
        
        # Detectar balas y sus direcciones
        neighborhood_types = [
            int(perception[AgentConsts.NEIGHBORHOOD_UP]),
            int(perception[AgentConsts.NEIGHBORHOOD_DOWN]),
            int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]),
            int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        ]
        
        neighborhood_dists = [
            perception[AgentConsts.NEIGHBORHOOD_DIST_UP],
            perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN],
            perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT],
            perception[AgentConsts.NEIGHBORHOOD_DIST_LEFT]
        ]
        
        # Encontrar la bala más cercana
        shell_direction = None
        min_dist = float('inf')
        
        for i in range(4):
            if neighborhood_types[i] == AgentConsts.SHELL and neighborhood_dists[i] < min_dist:
                min_dist = neighborhood_dists[i]
                shell_direction = i
        
        # Índice 0 (UP) → Opuesto es DOWN (pero con Y invertida, así que UP)
        escape_actions = [
            AgentConsts.MOVE_UP,      # Opuesto a UP (Y invertida)
            AgentConsts.MOVE_DOWN,    # Opuesto a DOWN (Y invertida)
            AgentConsts.MOVE_LEFT,    # Opuesto a RIGHT
            AgentConsts.MOVE_RIGHT    # Opuesto a LEFT
        ]
        
        if shell_direction is not None:
            action = escape_actions[shell_direction]
            print(f"[ESCAPE] Bala detectada en dirección {shell_direction} a distancia {min_dist:.1f}. Escapando")
        else:
            action = AgentConsts.NO_MOVE
        
        return action, False

    def Transit(self, perception, map):
        """
        Vuelve a ATTACK cuando ya no hay balas cercanas.
        """
        if len(perception) < 8:
            return self.id
        
        neighborhood_vals = [
            int(perception[AgentConsts.NEIGHBORHOOD_UP]),
            int(perception[AgentConsts.NEIGHBORHOOD_DOWN]),
            int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]),
            int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        ]
        
        has_shell_threat = AgentConsts.SHELL in neighborhood_vals
        
        if not has_shell_threat or self.escape_time > self.max_escape_time:
            print("[ESCAPE] Amenaza neutralizada. Volviendo a ATTACK")
            return "AttackTarget"
        
        return self.id

    def End(self):
        print("=== FINALIZANDO ESTADO: ESCAPE ===")

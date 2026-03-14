from StateMachine.State import State
from States.AgentConsts import AgentConsts
import math


class ShootAndOrient(State):
    """
    Estado para disparar y orientarse.
    Se usa cuando el agente detecta un objetivo alineado o necesita defenderse.
    """

    def __init__(self, id):
        super().__init__(id)
        self.orient_time = 0
        self.max_orient_time = 0.5  # Máximo tiempo orientándose

    def Start(self, agent):
        print("=== INICIANDO ESTADO: SHOOT_AND_ORIENT ===")
        self.orient_time = 0

    def Update(self, perception, map, agent):
        """
        Intenta alinearse con el objetivo y disparar.
        Y está invertida en el motor.
        """
        if len(perception) < 21:
            return AgentConsts.NO_MOVE, False
        
        # TIME está en índice 20
        if len(perception) > AgentConsts.TIME:
            self.orient_time += perception[AgentConsts.TIME]
        
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]
        
        # Detectar el objetivo válido (CC primero, luego Player)
        cc_alive = cc_x >= 0 and cc_y >= 0
        player_alive = player_x >= 0 and player_y >= 0
        
        if cc_alive:
            target_x = cc_x
            target_y = cc_y
            target_name = "CommandCenter"
        elif player_alive:
            target_x = player_x
            target_y = player_y
            target_name = "Player"
        else:
            return AgentConsts.NO_MOVE, False
        
        dx = target_x - agent_x
        dy = target_y - agent_y
        distance = math.sqrt(dx**2 + dy**2)
        
        can_fire = perception[AgentConsts.CAN_FIRE] == 1.0 or perception[AgentConsts.CAN_FIRE] == 1
        
        # Si está alineado horizontalmente (dy pequeño), disparar sin moverse
        if abs(dy) < 1.0 and abs(dx) > 0.5:
            print(f"[SHOOT] Alineado HORIZONTALMENTE con {target_name}. Disparando.")
            return AgentConsts.NO_MOVE, can_fire
        
        # Cuando dy < 0, target está ARRIBA (en pantalla visualmente arriba)
        if abs(dx) < 1.0 and abs(dy) > 0.5:
            print(f"[SHOOT] Alineado VERTICALMENTE con {target_name}. Disparando.")
            return AgentConsts.NO_MOVE, can_fire
        
        # Si no está alineado, moverse hacia la alineación
        if abs(dx) > abs(dy):
            # Diferencia horizontal es mayor
            action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
            print(f"[SHOOT] No alineado. Moviendo HORIZONTALMENTE hacia {target_name}.")
        else:
            # Diferencia vertical es mayor
            # INVERTIDA: dy > 0 (abajo en pantalla) → MOVE_UP
            #           dy < 0 (arriba en pantalla) → MOVE_DOWN
            action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
            print(f"[SHOOT] No alineado. Moviendo VERTICALMENTE hacia {target_name}.")
        
        print(f"[SHOOT] {target_name}@({target_x:.1f},{target_y:.1f}) | Agent@({agent_x:.1f},{agent_y:.1f}) | Dist:{distance:.1f} | Action:{action}")
        
        return action, can_fire

    def Transit(self, perception, map):
        """
        Transita cuando:
        - Tiempo límite se alcanza: volver a ATTACK
        - Si hay amenaza: ir a ESCAPE
        """
        if len(perception) < 8:
            return self.id
        
        # Chequear amenaza
        neighborhood_vals = [
            int(perception[AgentConsts.NEIGHBORHOOD_UP]),
            int(perception[AgentConsts.NEIGHBORHOOD_DOWN]),
            int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]),
            int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        ]
        
        has_shell_threat = AgentConsts.SHELL in neighborhood_vals
        if has_shell_threat:
            print("[SHOOT] ¡Bala detectada! Cambiando a ESCAPE")
            return "Escape"
        
        # Si tiempo límite se alcanza, volver a ataque
        if self.orient_time > self.max_orient_time:
            print("[SHOOT] Tiempo de orientación alcanzado. Volviendo a ATTACK")
            return "AttackTarget"
        
        return self.id

    def End(self):
        print("=== FINALIZANDO ESTADO: SHOOT_AND_ORIENT ===")

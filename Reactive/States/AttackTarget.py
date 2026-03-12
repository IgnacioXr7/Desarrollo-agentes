from StateMachine.State import State
from States.AgentConsts import AgentConsts
import math


class AttackTarget(State):
    """
    Estado para atacar al Command Center o al Jugador.
    VERSIÓN FINAL ACTUALIZADA:
    - TIME está en índice 21 (no 20)
    - ORIENTATION en índice 20
    - Bloques son 2x2
    - Mejor manejo de UNBREAKABLE
    - Dispara incluso a 1 casilla (dentro del bloque 2x2)
    """

    def __init__(self, id):
        super().__init__(id)
        self.target_x = None
        self.target_y = None
        self.last_direction = AgentConsts.NO_MOVE
        self.stuck_counter = 0
        self.last_position = (0, 0)
        self.blocked_direction_counter = 0
        

    def Start(self, agent):
        print("=== INICIANDO ESTADO: ATTACK ===")

    def Update(self, perception, map, agent):
        """
        Mueve hacia el Command Center o Jugador.
        Y ESTÁ INVERTIDA en el motor.
        Dispara ladrillos incluso cuando está a 1 casilla (bloques 2x2).
        """
        if len(perception) < 22:  # Ahora necesitamos hasta índice 21
            return AgentConsts.NO_MOVE, False
        
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        
        if math.isnan(agent_x) or math.isnan(agent_y):
            return AgentConsts.NO_MOVE, False
        
        # Detectar atoramiento
        current_position = (agent_x, agent_y)
        if current_position == self.last_position:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_position = current_position
        
        # PRIORIDAD: 1) Command Center, 2) Player, 3) Nada (salida)
        cc_alive = cc_x >= 0 and cc_y >= 0
        player_alive = player_x >= 0 and player_y >= 0
        
        if cc_alive:
            # Comando Center vivo → atacar CC (PRIORIDAD 1)
            target_x = cc_x
            target_y = cc_y
            target_name = "CommandCenter"
        elif not player_alive or not cc_alive:
            # Uno de los 2 muertos → ir a salida (PRIORIDAD 3)
            print("[ATTACK] ✓ Ambos objetivos destruidos. Transicionando a GoToExit")
            return AgentConsts.NO_MOVE, False
        else:
            target_x = player_x
            target_y = player_y
            target_name = "Player"
        
        # Calcular diferencias
        dx = target_x - agent_x
        dy = target_y - agent_y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Obtener contexto vecinal (CONVERTIR A INT)
        neighborhood_up = int(perception[AgentConsts.NEIGHBORHOOD_UP])
        neighborhood_down = int(perception[AgentConsts.NEIGHBORHOOD_DOWN])
        neighborhood_right = int(perception[AgentConsts.NEIGHBORHOOD_RIGHT])
        neighborhood_left = int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        
        can_fire_value = perception[AgentConsts.CAN_FIRE]
        can_fire = (can_fire_value == 1 or can_fire_value == 1.0)
        
        #    el motor requiere MOVE_DOWN (2)
        if abs(dx) > abs(dy):
            preferred_action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
            secondary_action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
        else:
            preferred_action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
            secondary_action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
        
        # LÓGICA ESPECIAL: Si está muy cerca del objetivo (< 2 casillas)
        # y hay BRICK alrededor, DISPARA obligatoriamente
        if distance < 2.0 and can_fire:
            # Está prácticamente en el objetivo, intenta disparar a BRICK cercano
            brick_directions = []
            if neighborhood_up == AgentConsts.BRICK:
                brick_directions.append((AgentConsts.MOVE_UP, "UP"))
            if neighborhood_down == AgentConsts.BRICK:
                brick_directions.append((AgentConsts.MOVE_DOWN, "DOWN"))
            if neighborhood_right == AgentConsts.BRICK:
                brick_directions.append((AgentConsts.MOVE_RIGHT, "RIGHT"))
            if neighborhood_left == AgentConsts.BRICK:
                brick_directions.append((AgentConsts.MOVE_LEFT, "LEFT"))
            
            if brick_directions:
                # Hay BRICKs alrededor, intenta disparar al más cercano a la dirección del objetivo
                if abs(dx) > abs(dy):
                    # Objetivo es más horizontal
                    preferred_brick = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                else:
                    # Objetivo es más vertical (Y INVERTIDA)
                    preferred_brick = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
                
                # Buscar si el BRICK preferido está disponible
                for action, direction_name in brick_directions:
                    if action == preferred_brick:
                        print(f"[ATTACK] ¡MUY CERCA! ({distance:.2f}). Disparando BRICK {direction_name} hacia objetivo")
                        self.last_direction = action
                        return action, True
                
                # Si no está el preferido, dispara al primer BRICK disponible
                action, direction_name = brick_directions[0]
                print(f"[ATTACK] ¡MUY CERCA! ({distance:.2f}). Disparando BRICK {direction_name} (alternativa)")
                self.last_direction = action
                return action, True
        
        # Navegar normalmente si no está muy cerca o no hay BRICKs
        action, should_fire = self._navigate_and_attack(
            preferred_action, 
            secondary_action,
            neighborhood_up, neighborhood_down, neighborhood_right, neighborhood_left,
            can_fire
        )
        
        # DEBUG
        print(f"[ATTACK] {target_name}@({target_x:.1f},{target_y:.1f}) | Agent@({agent_x:.1f},{agent_y:.1f}) | Dist:{distance:.1f} | Action:{action} | Fire:{should_fire}")
        
        self.last_direction = action
        return action, should_fire
    
    def _navigate_and_attack(self, preferred, secondary, n_up, n_down, n_right, n_left, can_fire):
        """
        Navegación inteligente con 4 prioridades.
        Dispara a BRICK cuando es necesario, incluso cuando está bloqueado.
        """
        
        # Solo UNBREAKABLE bloquea realmente
        blocked_up = n_up == AgentConsts.UNBREAKABLE
        blocked_down = n_down == AgentConsts.UNBREAKABLE
        blocked_right = n_right == AgentConsts.UNBREAKABLE
        blocked_left = n_left == AgentConsts.UNBREAKABLE
        
        # BRICK es destructible
        brick_up = n_up == AgentConsts.BRICK
        brick_down = n_down == AgentConsts.BRICK
        brick_right = n_right == AgentConsts.BRICK
        brick_left = n_left == AgentConsts.BRICK
        
        # PRIORIDAD 1: Dirección preferida
        if preferred == AgentConsts.MOVE_UP:
            if not blocked_up:
                should_fire = can_fire and brick_up
                return AgentConsts.MOVE_UP, should_fire
        elif preferred == AgentConsts.MOVE_DOWN:
            if not blocked_down:
                should_fire = can_fire and brick_down
                return AgentConsts.MOVE_DOWN, should_fire
        elif preferred == AgentConsts.MOVE_RIGHT:
            if not blocked_right:
                should_fire = can_fire and brick_right
                return AgentConsts.MOVE_RIGHT, should_fire
        elif preferred == AgentConsts.MOVE_LEFT:
            if not blocked_left:
                should_fire = can_fire and brick_left
                return AgentConsts.MOVE_LEFT, should_fire
        
        # PRIORIDAD 2: Dirección secundaria
        if secondary == AgentConsts.MOVE_UP:
            if not blocked_up:
                should_fire = can_fire and brick_up
                return AgentConsts.MOVE_UP, should_fire
        elif secondary == AgentConsts.MOVE_DOWN:
            if not blocked_down:
                should_fire = can_fire and brick_down
                return AgentConsts.MOVE_DOWN, should_fire
        elif secondary == AgentConsts.MOVE_RIGHT:
            if not blocked_right:
                should_fire = can_fire and brick_right
                return AgentConsts.MOVE_RIGHT, should_fire
        elif secondary == AgentConsts.MOVE_LEFT:
            if not blocked_left:
                should_fire = can_fire and brick_left
                return AgentConsts.MOVE_LEFT, should_fire
        
        # PRIORIDAD 3: Cualquier dirección abierta
        if not blocked_up:
            return AgentConsts.MOVE_UP, can_fire and brick_up
        elif not blocked_down:
            return AgentConsts.MOVE_DOWN, can_fire and brick_down
        elif not blocked_right:
            return AgentConsts.MOVE_RIGHT, can_fire and brick_right
        elif not blocked_left:
            return AgentConsts.MOVE_LEFT, can_fire and brick_left
        
        # PRIORIDAD 4: Completamente rodeado - Disparar a BRICK para escapar
        if can_fire:
            if brick_up:
                return AgentConsts.MOVE_UP, True
            elif brick_down:
                return AgentConsts.MOVE_DOWN, True
            elif brick_right:
                return AgentConsts.MOVE_RIGHT, True
            elif brick_left:
                return AgentConsts.MOVE_LEFT, True
        
        return AgentConsts.NO_MOVE, False

    def Transit(self, perception, map):
        """Transita a ESCAPE si hay amenaza, a EXIT si objetivo destruido"""
        if len(perception) < 21:
            return self.id
        
        neighborhood_vals = [
            int(perception[AgentConsts.NEIGHBORHOOD_UP]),
            int(perception[AgentConsts.NEIGHBORHOOD_DOWN]),
            int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]),
            int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        ]
        
        has_shell_threat = AgentConsts.SHELL in neighborhood_vals
        if has_shell_threat:
            print("[ATTACK] ⚠️  ¡BALA CERCANA! Cambiando a ESCAPE")
            return "Escape"
        
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        
        cc_alive = cc_x >= 0 and cc_y >= 0
        player_alive = player_x >= 0 and player_y >= 0
        
        if not cc_alive or not player_alive:
            print("[ATTACK] ✓ Objetivos destruidos. Yendo a EXIT")
            return "GoToExit"
        
        return self.id

    def End(self):
        print("=== FINALIZANDO ESTADO: ATTACK ===")

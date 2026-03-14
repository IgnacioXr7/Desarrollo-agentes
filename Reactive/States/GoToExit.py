from StateMachine.State import State
from States.AgentConsts import AgentConsts
import math


class GoToExit(State):
    """
    Estado para ir hacia la salida una vez destruidos los objetivos.
    VERSIÓN FINAL ACTUALIZADA:
    - TIME está en índice 21 (no 20)
    - ORIENTATION en índice 20
    - Bloques son 2x2
    - Mejor manejo de UNBREAKABLE (no intenta infinitamente)
    - Dispara a BRICKs en el camino
    """

    def __init__(self, id):
        super().__init__(id)
        self.blocked_direction_counter = {}  # Contar intentos en cada dirección bloqueada

    def Start(self, agent):
        print("=== INICIANDO ESTADO: GO_TO_EXIT ===")
        self.blocked_direction_counter = {}

    def Update(self, perception, map, agent):
        """
        Se mueve hacia la salida (EXIT).
        Y está invertida en el motor.
        Evita direcciones que siempre están bloqueadas.
        """
        if len(perception) < 21:
            print(f"[EXIT] Error: Percepción incompleta (longitud: {len(perception)})")
            return AgentConsts.NO_MOVE, False
        
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        exit_x = perception[AgentConsts.EXIT_X]
        exit_y = perception[AgentConsts.EXIT_Y]
        
        # Si salida no está disponible
        if exit_x < 0 or exit_y < 0:
            print("[EXIT] Salida no disponible")
            return AgentConsts.NO_MOVE, False
        
        # Calcular dirección hacia la salida
        dx = exit_x - agent_x
        dy = exit_y - agent_y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Obtener contexto vecinal
        neighborhood_up = int(perception[AgentConsts.NEIGHBORHOOD_UP])
        neighborhood_down = int(perception[AgentConsts.NEIGHBORHOOD_DOWN])
        neighborhood_right = int(perception[AgentConsts.NEIGHBORHOOD_RIGHT])
        neighborhood_left = int(perception[AgentConsts.NEIGHBORHOOD_LEFT])
        
        can_fire = perception[AgentConsts.CAN_FIRE] == 1.0 or perception[AgentConsts.CAN_FIRE] == 1
        
        # ⚠️ Y INVERTIDA: cuando dy < 0 (salida arriba), motor requiere MOVE_DOWN
        if abs(dx) > abs(dy):
            # Diferencia horizontal es mayor
            preferred_action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
            secondary_action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
        else:
            # Diferencia vertical es mayor
            # INVERTIDA: dy > 0 (salida abajo en pantalla) → MOVE_UP
            #           dy < 0 (salida arriba en pantalla) → MOVE_DOWN
            preferred_action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
            secondary_action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
        
        # LÓGICA ESPECIAL: Si está MUY CERCA de la salida (< 2 casillas)
        if distance < 2.0:
            print(f"[EXIT] ¡MUY CERCA DE LA SALIDA! ({distance:.2f}) Moviéndose directamente")
            
            # A esta distancia, intenta moverse directamente hacia la salida
            # sin importar BRICK/UNBREAKABLE, solo para entrar
            if abs(dx) > abs(dy):
                # Más horizontal
                action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                print(f"[EXIT] Movimiento final HORIZONTAL hacia salida")
            else:
                # Más vertical (Y INVERTIDA)
                action = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN
                print(f"[EXIT] Movimiento final VERTICAL hacia salida")
            
            # NO dispara cuando está casi en la meta, solo se mueve
            should_fire = False
            print(f"[EXIT] Salida@({exit_x:.1f},{exit_y:.1f}) | Agent@({agent_x:.1f},{agent_y:.1f}) | Dist:{distance:.1f} | Action:{action} | Fire:{should_fire}")
            return action, should_fire
        
        # Navegar normalmente si está lejos
        action, should_fire = self._navigate_smart(
            preferred_action,
            secondary_action,
            neighborhood_up, neighborhood_down, neighborhood_right, neighborhood_left,
            can_fire
        )
        
        print(f"[EXIT] Salida@({exit_x:.1f},{exit_y:.1f}) | Agent@({agent_x:.1f},{agent_y:.1f}) | Dist:{distance:.1f} | Action:{action} | Fire:{should_fire}")
        
        return action, should_fire
    
    def _navigate_smart(self, preferred, secondary, n_up, n_down, n_right, n_left, can_fire):
        """
        Navegación inteligente:
        1. Intenta preferida
        2. Intenta secundaria
        3. Intenta cualquier abierta
        4. Dispara a BRICK si está completamente bloqueado
        
        Evita quedarse atrapado intentando infinitamente una dirección bloqueada.
        """
        
        blocked_up = n_up == AgentConsts.UNBREAKABLE
        blocked_down = n_down == AgentConsts.UNBREAKABLE
        blocked_right = n_right == AgentConsts.UNBREAKABLE
        blocked_left = n_left == AgentConsts.UNBREAKABLE
        
        brick_up = n_up == AgentConsts.BRICK
        brick_down = n_down == AgentConsts.BRICK
        brick_right = n_right == AgentConsts.BRICK
        brick_left = n_left == AgentConsts.BRICK
        
        # PRIORIDAD 1: Preferida (si no está bloqueada por UNBREAKABLE)
        if preferred == AgentConsts.MOVE_UP and not blocked_up:
            should_fire = can_fire and brick_up
            return AgentConsts.MOVE_UP, should_fire
        elif preferred == AgentConsts.MOVE_DOWN and not blocked_down:
            should_fire = can_fire and brick_down
            return AgentConsts.MOVE_DOWN, should_fire
        elif preferred == AgentConsts.MOVE_RIGHT and not blocked_right:
            should_fire = can_fire and brick_right
            return AgentConsts.MOVE_RIGHT, should_fire
        elif preferred == AgentConsts.MOVE_LEFT and not blocked_left:
            should_fire = can_fire and brick_left
            return AgentConsts.MOVE_LEFT, should_fire
        
        # PRIORIDAD 2: Secundaria (si no está bloqueada)
        if secondary == AgentConsts.MOVE_UP and not blocked_up:
            should_fire = can_fire and brick_up
            return AgentConsts.MOVE_UP, should_fire
        elif secondary == AgentConsts.MOVE_DOWN and not blocked_down:
            should_fire = can_fire and brick_down
            return AgentConsts.MOVE_DOWN, should_fire
        elif secondary == AgentConsts.MOVE_RIGHT and not blocked_right:
            should_fire = can_fire and brick_right
            return AgentConsts.MOVE_RIGHT, should_fire
        elif secondary == AgentConsts.MOVE_LEFT and not blocked_left:
            should_fire = can_fire and brick_left
            return AgentConsts.MOVE_LEFT, should_fire
        
        # PRIORIDAD 3: Cualquier dirección abierta (no bloqueada por UNBREAKABLE)
        if not blocked_up:
            return AgentConsts.MOVE_UP, can_fire and brick_up
        elif not blocked_down:
            return AgentConsts.MOVE_DOWN, can_fire and brick_down
        elif not blocked_right:
            return AgentConsts.MOVE_RIGHT, can_fire and brick_right
        elif not blocked_left:
            return AgentConsts.MOVE_LEFT, can_fire and brick_left
        
        # PRIORIDAD 4: Completamente rodeado por UNBREAKABLE
        # Disparar a BRICK si lo hay para crear ruta de escape
        if can_fire:
            if brick_up:
                return AgentConsts.MOVE_UP, True
            elif brick_down:
                return AgentConsts.MOVE_DOWN, True
            elif brick_right:
                return AgentConsts.MOVE_RIGHT, True
            elif brick_left:
                return AgentConsts.MOVE_LEFT, True
        
        # Último recurso: no hay nada que hacer
        print(f"[EXIT] ⚠️ Completamente bloqueado, sin forma de avanzar")
        return AgentConsts.NO_MOVE, False

    def Transit(self, perception, map):
        """
        Se mantiene yendo a la salida hasta ganar.
        """
        return self.id

    def End(self):
        print("=== FINALIZANDO ESTADO: GO_TO_EXIT - ¡VICTORIA! ===")

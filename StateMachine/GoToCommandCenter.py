
from StateMachine.constantes import *
from StateMachine.State import State
from collections import deque

class GoToCommandCenter(State):
    """
    Navega hacia la CC.
    Usa las coordenadas directamente para decidir dirección,
    y la percepción de vecinos para saber si hay obstáculo inmediato.
    Dispara si CAN_FIRE o si hay ladrillo en la dirección de movimiento.
    """

    MAP_SIZE = 15

    def __init__(self, id):
        super().__init__(id)
        self.next_action = DO_NOTHING
        self.recalc_timer = 0

    def Start(self, agent):
        print("Inicio del estado: GoToCommandCenter")
        self.next_action = DO_NOTHING
        self.recalc_timer = 0

    # ------------------------------------------------------------------
    # Percepción: qué hay en cada dirección adyacente
    # ------------------------------------------------------------------

    def _neighbor(self, perception, direction):
        mapping = {
            MOVE_UP:    NEIGHBORHOOD_UP,
            MOVE_DOWN:  NEIGHBORHOOD_DOWN,
            MOVE_RIGHT: NEIGHBORHOOD_RIGHT,
            MOVE_LEFT:  NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[direction]])

    def _is_blocked(self, perception, direction):
        """Solo UNBREAKABLE bloquea. BRICK se puede destruir."""
        return self._neighbor(perception, direction) == UNBREAKABLE

    def _is_brick(self, perception, direction):
        return self._neighbor(perception, direction) == BRICK

    # ------------------------------------------------------------------
    # Navegación hacia la CC usando coordenadas + percepción
    # ------------------------------------------------------------------

    def _choose_action(self, perception):
        ax = perception[AGENT_X]
        ay = perception[AGENT_Y]
        cx = perception[COMMAND_CENTER_X]
        cy = perception[COMMAND_CENTER_Y]

        dx = cx - ax   # positivo = CC está a la derecha
        dy = cy - ay   # positivo = CC está abajo (Y crece hacia abajo)

        # Ordenar por eje de mayor distancia
        if abs(dx) >= abs(dy):
            primary   = MOVE_RIGHT if dx > 0 else MOVE_LEFT
            secondary = MOVE_DOWN if dy < 0 else MOVE_UP
        else:
            primary   = MOVE_DOWN if dy < 0 else MOVE_UP
            secondary = MOVE_RIGHT if dx > 0 else MOVE_LEFT

        # Intentar primary, luego secondary, luego los otros dos
        all_dirs = [primary, secondary]
        for d in (MOVE_UP, MOVE_DOWN, MOVE_RIGHT, MOVE_LEFT):
            if d not in all_dirs:
                all_dirs.append(d)

        for action in all_dirs:
            if not self._is_blocked(perception, action):
                return action

        return DO_NOTHING  # completamente rodeado de indestructibles

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def Update(self, perception, map, agent):
        can_fire = bool(perception[CAN_FIRE])

        action = self._choose_action(perception)

        brick_ahead = action != DO_NOTHING and self._is_brick(perception, action)
        shoot = can_fire or brick_ahead

        return action, shoot

    # ------------------------------------------------------------------
    # Transit
    # ------------------------------------------------------------------

    def Transit(self, perception, map):
        return self.id

    def End(self):
        print("Fin del estado: GoToCommandCenter")

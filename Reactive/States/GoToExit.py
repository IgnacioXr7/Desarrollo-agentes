from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToExit(State):

    def __init__(self, id):
        super().__init__(id)
        self.last_pos = None
        self.stuck_counter = 0
        self.pos_history = []       # historial para detectar oscilación
        self.escape_move = None     # movimiento forzado para salir del bucle
        self.escape_steps = 0       # cuántos ticks queda activo el escape

    def Start(self, agent):
        print("Inicio del estado: GoToExit")
        self.last_pos = None
        self.stuck_counter = 0
        self.pos_history = []
        self.escape_move = None
        self.escape_steps = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _neighbor(self, perception, move):
        mapping = {
            AgentConsts.MOVE_UP: AgentConsts.NEIGHBORHOOD_UP,
            AgentConsts.MOVE_DOWN: AgentConsts.NEIGHBORHOOD_DOWN,
            AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
            AgentConsts.MOVE_LEFT: AgentConsts.NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[move]])

    def _is_free(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell not in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE,
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE,
        )

    def _is_brick(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (AgentConsts.BRICK, AgentConsts.SEMI_BREKABLE)

    def _is_passable(self, perception, move):
        """Libre O ladrillo (se puede abrir disparando)."""
        return self._is_free(perception, move) or self._is_brick(perception, move)

    def _cc_alive(self, perception):
        cx = float(perception[AgentConsts.COMMAND_CENTER_X])
        cy = float(perception[AgentConsts.COMMAND_CENTER_Y])
        return not (cx < 0 or cy < 0)

    def _dist_to_exit(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])
        return abs(ax - ex) + abs(ay - ey)

    def _preferred_moves(self, perception):
        """Misma lógica que GoToCC pero apuntando a EXIT."""
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        tx = float(perception[AgentConsts.EXIT_X])
        ty = float(perception[AgentConsts.EXIT_Y])

        dx = tx - ax
        dy = ty - ay
        eps = 0.25

        dir_x = None
        dir_y = None

        if abs(dx) > eps:
            dir_x = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
        if abs(dy) > eps:
            dir_y = AgentConsts.MOVE_DOWN if dy < 0 else AgentConsts.MOVE_UP

        if dir_x is not None and dir_y is not None:
            return [dir_x, dir_y] if abs(dx) >= abs(dy) else [dir_y, dir_x]
        if dir_x is not None:
            return [dir_x]
        if dir_y is not None:
            return [dir_y]
        return []

    def _direct_move(self, perception):
        """Dirección directa por coordenadas, sin consultar percepción."""
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])
        dx = ex - ax
        dy = ey - ay
        if abs(dx) >= abs(dy):
            return AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
        return AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN

    def _is_oscillating(self):
        """
        Detecta oscilación: el agente alterna entre dos posiciones
        (A→B→A→B...) sin avanzar hacia el objetivo.
        """
        if len(self.pos_history) < 4:
            return False
        h = self.pos_history
        # patrón: pos[-4] == pos[-2] y pos[-3] == pos[-1] y son distintas
        return h[-4] == h[-2] and h[-3] == h[-1] and h[-4] != h[-3]

    def _dist_after_move(self, perception, move):
        """Distancia Manhattan a la salida tras aplicar el movimiento."""
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])
        if move == AgentConsts.MOVE_UP:
            ay += 1
        elif move == AgentConsts.MOVE_DOWN:
            ay -= 1
        elif move == AgentConsts.MOVE_RIGHT:
            ax += 1
        elif move == AgentConsts.MOVE_LEFT:
            ax -= 1
        return abs(ax - ex) + abs(ay - ey)

    def _choose_escape_move(self, perception):
        """
        Cuando hay oscilación, evalúa TODOS los movimientos posibles
        (libres y ladrillos) ordenados por distancia a la salida.
        Así evita elegir un perpendicular que aleja del objetivo.
        """
        candidates = []
        for move in (
            AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT,
        ):
            if self._is_free(perception, move):
                candidates.append((self._dist_after_move(perception, move), 0, move, False))
            elif self._is_brick(perception, move):
                candidates.append((self._dist_after_move(perception, move), 1, move, True))
            # UNBREAKABLE se descarta

        if not candidates:
            return AgentConsts.NO_MOVE, False

        # Menor distancia primero; libre antes que ladrillo en empate
        candidates.sort(key=lambda x: (x[0], x[1]))
        _, _, move, shoot = candidates[0]
        return move, shoot

    def _choose_action(self, perception):
        """Misma lógica que GoToCC."""
        preferred = self._preferred_moves(perception)

        for move in preferred:
            if self._is_free(perception, move):
                return move, False

        for move in preferred:
            if self._is_brick(perception, move):
                return move, True

        for move in (
            AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT
        ):
            if self._is_free(perception, move):
                return move, False

        for move in (
            AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT
        ):
            if self._is_brick(perception, move):
                return move, True

        return AgentConsts.NO_MOVE, False

    # ------------------------------------------------------------------
    # State interface
    # ------------------------------------------------------------------

    def Update(self, perception, game_map, agent):
        dist = self._dist_to_exit(perception)
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        # Cerca: forzar movimiento directo ignorando percepción.
        # Radio 2.5 cubre el caso donde la salida está a 2 casillas pero
        # la percepción ve UNBREAKABLE (borde del mundo) en esa dirección.
        if dist <= 2.5:
            action = self._direct_move(perception)
            print(f"[GoToExit] agente=({ax:.1f},{ay:.1f}) exit=({ex:.1f},{ey:.1f}) dist={dist:.2f} -> forzando {action}")
            return action, False

        current_pos = (round(ax, 2), round(ay, 2))

        # Actualizar historial (guardamos posiciones redondeadas para comparar)
        self.pos_history.append(current_pos)
        if len(self.pos_history) > 6:
            self.pos_history.pop(0)

        # Stuck counter (posición idéntica)
        if self.last_pos is not None and self.last_pos == current_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_pos = current_pos

        # --- Modo escape activo ---
        if self.escape_steps > 0:
            self.escape_steps -= 1
            can_fire = bool(perception[AgentConsts.CAN_FIRE])
            shoot = self._is_brick(perception, self.escape_move)
            print(f"[GoToExit] agente=({ax:.1f},{ay:.1f}) exit=({ex:.1f},{ey:.1f}) dist={dist:.2f} ESCAPE action={self.escape_move} steps_left={self.escape_steps}")
            return self.escape_move, can_fire and shoot

        # --- Detectar oscilación o atasco y activar escape ---
        if self._is_oscillating() or self.stuck_counter > 5:
            escape_action, escape_shoot = self._choose_escape_move(perception)
            if escape_action != AgentConsts.NO_MOVE:
                self.escape_move = escape_action
                self.escape_steps = 4   # mantener el escape 4 ticks
                self.pos_history.clear()
                self.stuck_counter = 0
                can_fire = bool(perception[AgentConsts.CAN_FIRE])
                print(f"[GoToExit] agente=({ax:.1f},{ay:.1f}) exit=({ex:.1f},{ey:.1f}) dist={dist:.2f} OSCILACION DETECTADA -> escape {escape_action}")
                return escape_action, can_fire and escape_shoot

        # --- Movimiento normal ---
        action, must_shoot = self._choose_action(perception)
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        print(f"[GoToExit] agente=({ax:.1f},{ay:.1f}) exit=({ex:.1f},{ey:.1f}) dist={dist:.2f} action={action} shoot={can_fire and must_shoot}")
        return action, can_fire and must_shoot

    def Transit(self, perception, game_map):
       # if self._cc_alive(perception):
        #    return "GoToCC"
        return self.id

    def End(self):
        print("Fin del estado: GoToExit")

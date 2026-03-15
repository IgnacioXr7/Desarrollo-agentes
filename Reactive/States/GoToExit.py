from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToExit(State):

    def __init__(self, id):
        super().__init__(id)
        self.last_pos = None
        self.last_action = None
        self.stuck_counter = 0
        self.pos_history = []

        # mantener rodeo lateral varios pasos
        self.bypass_move = None
        self.bypass_steps = 0

    def Start(self, agent):
        print("Inicio del estado: GoToExit")
        self.last_pos = None
        self.last_action = None
        self.stuck_counter = 0
        self.pos_history = []
        self.bypass_move = None
        self.bypass_steps = 0

    # ---------------------------------------------------------
    # Utilidades básicas
    # ---------------------------------------------------------

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
            AgentConsts.SEMI_BREKABLE
        )

    def _is_brick(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _is_unbreakable(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE
        )

    def _all_moves(self):
        return [
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ]

    def _opposite(self, move):
        if move == AgentConsts.MOVE_UP:
            return AgentConsts.MOVE_DOWN
        if move == AgentConsts.MOVE_DOWN:
            return AgentConsts.MOVE_UP
        if move == AgentConsts.MOVE_RIGHT:
            return AgentConsts.MOVE_LEFT
        if move == AgentConsts.MOVE_LEFT:
            return AgentConsts.MOVE_RIGHT
        return None

    # ---------------------------------------------------------
    # Geometría exacta
    # ---------------------------------------------------------

    def _agent_cell(self, perception):
        ax = int(round(float(perception[AgentConsts.AGENT_X])))
        ay = int(round(float(perception[AgentConsts.AGENT_Y])))
        return ax, ay

    def _exit_cell(self, perception):
        ex = int(round(float(perception[AgentConsts.EXIT_X])))
        ey = int(round(float(perception[AgentConsts.EXIT_Y])))
        return ex, ey

    def _next_cell_after_move(self, perception, move):
        ax, ay = self._agent_cell(perception)

        if move == AgentConsts.MOVE_UP:
            ay += 1
        elif move == AgentConsts.MOVE_DOWN:
            ay -= 1
        elif move == AgentConsts.MOVE_RIGHT:
            ax += 1
        elif move == AgentConsts.MOVE_LEFT:
            ax -= 1

        return ax, ay

    def _move_hits_exit(self, perception, move):
        return self._next_cell_after_move(perception, move) == self._exit_cell(perception)

    def _at_exit(self, perception):
        return self._agent_cell(perception) == self._exit_cell(perception)

    def _distance_after_move(self, perception, move):
        nx, ny = self._next_cell_after_move(perception, move)
        ex, ey = self._exit_cell(perception)
        return abs(ex - nx) + abs(ey - ny)

    # ---------------------------------------------------------
    # Direcciones prioritarias
    # ---------------------------------------------------------

    def _direct_moves(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        dx = ex - ax
        dy = ey - ay
        eps = 0.35

        horizontal = None
        vertical = None

        if abs(dx) > eps:
            horizontal = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT

        if abs(dy) > eps:
            vertical = AgentConsts.MOVE_UP if dy > 0 else AgentConsts.MOVE_DOWN

        if vertical is not None and horizontal is not None:
            if abs(dy) >= abs(dx):
                return vertical, horizontal
            return horizontal, vertical

        if vertical is not None:
            return vertical, horizontal

        if horizontal is not None:
            return horizontal, vertical

        return AgentConsts.NO_MOVE, None

    def _perpendicular_moves(self, primary):
        if primary in (AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN):
            return [AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT]

        if primary in (AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT):
            return [AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN]

        return self._all_moves()

    # ---------------------------------------------------------
    # Selección
    # ---------------------------------------------------------

    def _force_enter_exit(self, perception, can_fire):
        for move in self._all_moves():
            if self._move_hits_exit(perception, move):
                if self._is_free(perception, move):
                    return move, False
                if self._is_brick(perception, move) and can_fire:
                    return move, True
        return None

    def _best_of(self, perception, candidates, can_fire):
        scored = []
        recent = set(self.pos_history[-6:])

        for move in candidates:
            if move is None or move == AgentConsts.NO_MOVE:
                continue
            if self._is_unbreakable(perception, move):
                continue

            shoot = False
            if self._is_brick(perception, move):
                if not can_fire:
                    continue
                shoot = True

            score = self._distance_after_move(perception, move)
            next_pos = self._next_cell_after_move(perception, move)

            if self.last_action is not None and move == self._opposite(self.last_action):
                score += 4

            if next_pos in recent:
                score += 5

            if self._move_hits_exit(perception, move):
                score -= 100

            scored.append((score, move, shoot))

        if not scored:
            return AgentConsts.NO_MOVE, False

        scored.sort(key=lambda x: x[0])
        return scored[0][1], scored[0][2]

    def _choose_action(self, perception, can_fire):
        # 0) entrar exacto si se puede
        exact = self._force_enter_exit(perception, can_fire)
        if exact is not None:
            self.bypass_move = None
            self.bypass_steps = 0
            return exact

        primary, secondary = self._direct_moves(perception)

        # 1) mantener rodeo lateral si ya se eligió uno
        if self.bypass_move is not None and self.bypass_steps > 0:
            if self._is_free(perception, self.bypass_move):
                self.bypass_steps -= 1
                return self.bypass_move, False

            if self._is_brick(perception, self.bypass_move) and can_fire:
                self.bypass_steps -= 1
                return self.bypass_move, True

            self.bypass_move = None
            self.bypass_steps = 0

        # 2) camino directo
        if primary != AgentConsts.NO_MOVE:
            if self._is_free(perception, primary):
                return primary, False

            if self._is_brick(perception, primary):
                if can_fire:
                    return primary, True

        # 3) si el primario está bloqueado por irrompible, elegir lateral bueno y MANTENERLO
        if primary != AgentConsts.NO_MOVE and self._is_unbreakable(perception, primary):
            laterals = self._perpendicular_moves(primary)

            # ordenar laterales por cuál acerca más al exit
            laterals = sorted(laterals, key=lambda m: self._distance_after_move(perception, m))

            move, shoot = self._best_of(perception, laterals, can_fire)
            if move != AgentConsts.NO_MOVE:
                self.bypass_move = move
                self.bypass_steps = 3
                return move, shoot

        # 4) secundaria
        if secondary is not None:
            if self._is_free(perception, secondary):
                return secondary, False
            if self._is_brick(perception, secondary):
                if can_fire:
                    return secondary, True

        # 5) fallback global
        return self._best_of(perception, self._all_moves(), can_fire)

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def Update(self, perception, game_map, agent):
        if self._at_exit(perception):
            print("[GoToExit] salida alcanzada")
            return AgentConsts.NO_MOVE, False

        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        current_pos = (ax, ay)

        self.pos_history.append(self._agent_cell(perception))
        if len(self.pos_history) > 10:
            self.pos_history.pop(0)

        if self.last_pos is not None and self.last_pos == current_pos:
            self.stuck_counter += 1
        elif len(self.pos_history) >= 4 and self.pos_history[-1] == self.pos_history[-3]:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        # si está muy atascado, cancelar rodeo anterior
        if self.stuck_counter >= 6:
            self.bypass_move = None
            self.bypass_steps = 0

        action, shoot = self._choose_action(perception, can_fire)

        self.last_pos = current_pos
        if action != AgentConsts.NO_MOVE:
            self.last_action = action

        print(
            f"[GoToExit] pos={current_pos} stuck={self.stuck_counter} "
            f"bypass={self.bypass_move} steps={self.bypass_steps} "
            f"action={action} shoot={shoot}"
        )

        return action, shoot

    def Transit(self, perception, game_map):
        return self.id

    def End(self):
        print("Fin del estado: GoToExit")
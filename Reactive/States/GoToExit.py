from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToExit(State):

    def __init__(self, id):
        super().__init__(id)
        self.nextState = id
        self.last_pos = None
        self.stuck_counter = 0

    def Start(self, agent):
        print("=== INICIANDO ESTADO: GO TO EXIT ===")
        self.nextState = self.id
        self.last_pos = None
        self.stuck_counter = 0

        if not hasattr(agent, "direction"):
            agent.direction = AgentConsts.NEIGHBORHOOD_UP

    def _neighbor(self, perception, move):
        mapping = {
            AgentConsts.MOVE_UP: AgentConsts.NEIGHBORHOOD_UP,
            AgentConsts.MOVE_DOWN: AgentConsts.NEIGHBORHOOD_DOWN,
            AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
            AgentConsts.MOVE_LEFT: AgentConsts.NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[move]])

    def _move_to_neighborhood(self, move):
        if move == AgentConsts.MOVE_UP:
            return AgentConsts.NEIGHBORHOOD_UP
        if move == AgentConsts.MOVE_DOWN:
            return AgentConsts.NEIGHBORHOOD_DOWN
        if move == AgentConsts.MOVE_RIGHT:
            return AgentConsts.NEIGHBORHOOD_RIGHT
        if move == AgentConsts.MOVE_LEFT:
            return AgentConsts.NEIGHBORHOOD_LEFT
        return AgentConsts.NEIGHBORHOOD_UP

    def _is_hard_blocked(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE
        )

    def _is_brick(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _is_free(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell not in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE,
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _at_exit_zone(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        # usa == si tu juego exige casilla exacta
        return abs(ax - ex) <= 1.0 and abs(ay - ey) <= 1.0

    def _preferred_moves(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        dx = ex - ax
        dy = ey - ay

        moves = []

        # Prioriza el eje donde hay más diferencia
        if abs(dx) > abs(dy):
            if dx > 0:
                moves.append(AgentConsts.MOVE_RIGHT)
            elif dx < 0:
                moves.append(AgentConsts.MOVE_LEFT)

            if dy > 0:
                moves.append(AgentConsts.MOVE_UP)
            elif dy < 0:
                moves.append(AgentConsts.MOVE_DOWN)
        else:
            if dy > 0:
                moves.append(AgentConsts.MOVE_UP)
            elif dy < 0:
                moves.append(AgentConsts.MOVE_DOWN)

            if dx > 0:
                moves.append(AgentConsts.MOVE_RIGHT)
            elif dx < 0:
                moves.append(AgentConsts.MOVE_LEFT)

        # Añadir alternativas por si las principales fallan
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if move not in moves:
                moves.append(move)

        return moves

    def _choose_action(self, perception):
        if self._at_exit_zone(perception):
            return AgentConsts.NO_MOVE, False

        preferred = self._preferred_moves(perception)

        # 1) Intentar mover libremente hacia el exit
        for move in preferred:
            if self._is_free(perception, move):
                return move, False

        # 2) Si no se puede, intentar romper ladrillo en dirección útil
        for move in preferred:
            if self._is_brick(perception, move):
                return move, True

        # 3) Si todo está bloqueado, intentar cualquier libre
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_free(perception, move):
                return move, False

        # 4) Si no hay libres, intentar cualquier ladrillo
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_brick(perception, move):
                return move, True

        return AgentConsts.NO_MOVE, False

    def Update(self, perception, game_map, agent):
        self.nextState = self.id

        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        current_pos = (ax, ay)

        if self.last_pos is not None and self.last_pos == current_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        action, must_shoot = self._choose_action(perception)

        # Si está atascado, probar laterales antes que quedarse quieto
        if self.stuck_counter >= 3 and action == AgentConsts.NO_MOVE:
            for move in (
                AgentConsts.MOVE_UP,
                AgentConsts.MOVE_DOWN,
                AgentConsts.MOVE_RIGHT,
                AgentConsts.MOVE_LEFT
            ):
                if self._is_free(perception, move):
                    action = move
                    must_shoot = False
                    break

        self.last_pos = current_pos
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        if action != AgentConsts.NO_MOVE:
            agent.direction = self._move_to_neighborhood(action)

        print(
            f"[GoToExit] pos={current_pos} stuck={self.stuck_counter} "
            f"action={action} shoot={can_fire and must_shoot}"
        )

        return action, can_fire and must_shoot

    def Transit(self, perception, game_map):
        return self.nextState

    def End(self):
        print("=== FINALIZANDO ESTADO: GO TO EXIT ===")
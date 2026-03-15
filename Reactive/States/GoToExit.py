from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToExit(State):

    def __init__(self, id):
        super().__init__(id)
        self.last_pos = None
        self.stuck_counter = 0
        self.pos_history = []

    def Start(self, agent):
        print("Inicio del estado: GoToExit")
        self.last_pos = None
        self.stuck_counter = 0
        self.pos_history = []

    def _neighbor(self, perception, move):
        mapping = {
            AgentConsts.MOVE_UP: AgentConsts.NEIGHBORHOOD_UP,
            AgentConsts.MOVE_DOWN: AgentConsts.NEIGHBORHOOD_DOWN,
            AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
            AgentConsts.MOVE_LEFT: AgentConsts.NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[move]])

    def _is_hard_blocked(self, perception, move):
        cell = self._neighbor(perception, move)
        return cell in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE
        )

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

    def _next_pos(self, ax, ay, move):
        if move == AgentConsts.MOVE_UP:
            return ax, ay + 1
        if move == AgentConsts.MOVE_DOWN:
            return ax, ay - 1
        if move == AgentConsts.MOVE_RIGHT:
            return ax + 1, ay
        if move == AgentConsts.MOVE_LEFT:
            return ax - 1, ay
        return ax, ay

    def _distance(self, x1, y1, x2, y2):
        return abs(x2 - x1) + abs(y2 - y1)

    def _at_exit_zone(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        return abs(ax - ex) <= 1.0 and abs(ay - ey) <= 1.0

    def _is_looping(self):
        if len(self.pos_history) < 4:
            return False
        a, b, c, d = self.pos_history[-4:]
        return a == c and b == d and a != b

    def _choose_action(self, perception, force_break=False):
        if self._at_exit_zone(perception):
            return AgentConsts.NO_MOVE, False

        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        ex = float(perception[AgentConsts.EXIT_X])
        ey = float(perception[AgentConsts.EXIT_Y])

        actions = (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        )

        candidates = []

        current_dist = self._distance(ax, ay, ex, ey)

        for move in actions:
            if self._is_hard_blocked(perception, move):
                continue

            nx, ny = self._next_pos(ax, ay, move)
            new_dist = self._distance(nx, ny, ex, ey)

            # Penalizar retrocesos
            goes_away = new_dist > current_dist

            if self._is_free(perception, move):
                score = new_dist
                if goes_away:
                    score += 3
                candidates.append((score, move, False))

            elif self._is_brick(perception, move):
                # Penalización pequeña al ladrillo, no infinita
                score = new_dist + 0.8
                if force_break:
                    score -= 1.0
                if goes_away:
                    score += 3
                candidates.append((score, move, True))

        if not candidates:
            return AgentConsts.NO_MOVE, False

        candidates.sort(key=lambda x: x[0])
        _, move, shoot = candidates[0]
        return move, shoot

    def Update(self, perception, game_map, agent):
        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        current_pos = (ax, ay)

        self.pos_history.append(current_pos)
        if len(self.pos_history) > 6:
            self.pos_history.pop(0)

        if self.last_pos is not None and self.last_pos == current_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        looping = self._is_looping()
        force_break = looping or self.stuck_counter > 3

        action, must_shoot = self._choose_action(perception, force_break=force_break)

        self.last_pos = current_pos
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        print(
            f"[GoToExit] pos={current_pos} loop={looping} stuck={self.stuck_counter} "
            f"action={action} shoot={can_fire and must_shoot}"
        )
        return action, can_fire and must_shoot

    def Transit(self, perception, game_map):
        return self.id

    def End(self):
        print("Fin del estado: GoToExit")

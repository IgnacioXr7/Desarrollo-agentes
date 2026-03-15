from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToCC(State):

    def __init__(self, id):
        super().__init__(id)
        self.last_pos = None
        self.stuck_counter = 0

    def Start(self, agent):
        print("Inicio del estado: GoToCC")
        self.last_pos = None
        self.stuck_counter = 0

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

    def _player_near(self, perception):
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._neighbor(perception, move) == AgentConsts.PLAYER:
                return True
        return False


    def _cc_near(self, perception):
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._neighbor(perception, move) == AgentConsts.COMMAND_CENTER:
                return True
        return False

    def _cc_destroyed(self, perception):
        cx = float(perception[AgentConsts.COMMAND_CENTER_X])
        cy = float(perception[AgentConsts.COMMAND_CENTER_Y])
        return (cx < 0 or cy < 0) or (cx == 0 and cy == 0)

    def _preferred_moves(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        tx = float(perception[AgentConsts.COMMAND_CENTER_X])
        ty = float(perception[AgentConsts.COMMAND_CENTER_Y])

        dx = tx - ax
        dy = ty - ay
        eps = 0.25

        dir_x = None
        dir_y = None

        if abs(dx) > eps:
            dir_x = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT

        # En vuestro motor MOVE_DOWN baja Y
        if abs(dy) > eps:
            dir_y = AgentConsts.MOVE_DOWN if dy < 0 else AgentConsts.MOVE_UP

        preferred = []

        if dir_x is not None and dir_y is not None:
            if abs(dx) >= abs(dy):
                preferred = [dir_x, dir_y]
            else:
                preferred = [dir_y, dir_x]
        elif dir_x is not None:
            preferred = [dir_x]
        elif dir_y is not None:
            preferred = [dir_y]

        return preferred

    def _choose_action(self, perception):
        preferred = self._preferred_moves(perception)

        # 1) libres preferidos
        for move in preferred:
            if self._is_free(perception, move):
                return move, False

        # 2) ladrillo preferido
        for move in preferred:
            if self._is_brick(perception, move):
                return move, True

        # 3) cualquier libre
        for move in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_free(perception, move):
                return move, False

        # 4) cualquier ladrillo
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
        # Si el CC ya no existe, ir al exit
        if self._cc_destroyed(perception):
            return AgentConsts.NO_MOVE, False

        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        current_pos = (ax, ay)

        action, must_shoot = self._choose_action(perception)

        if self.last_pos is not None and self.last_pos == current_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        if self.stuck_counter > 5:
            for move in (
                AgentConsts.MOVE_RIGHT,
                AgentConsts.MOVE_LEFT,
                AgentConsts.MOVE_DOWN,
                AgentConsts.MOVE_UP
            ):
                if self._is_free(perception, move):
                    action = move
                    must_shoot = False
                    self.stuck_counter = 0
                    break
                if self._is_brick(perception, move):
                    action = move
                    must_shoot = True
                    self.stuck_counter = 0
                    break

        self.last_pos = current_pos
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        print(f"[GoToCC] action={action} shoot={can_fire and must_shoot}")
        return action, can_fire and must_shoot

    def Transit(self, perception, game_map):
        if self._cc_destroyed(perception):
            return "GoToExit"

        if self._cc_near(perception):
            return "Shoot"
        if self._player_near(perception):
            return "Shoot"

        return self.id

    def End(self):
        print("Fin del estado: GoToCC")

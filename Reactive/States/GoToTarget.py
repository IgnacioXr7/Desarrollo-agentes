from StateMachine.State import State
from States.AgentConsts import AgentConsts
from States.Shoot import Shoot

class GoToTarget(State):

    TARGET_CC = 0
    TARGET_EXIT = 1

    def __init__(self, id):
        super().__init__(id)
        self.target_x = None
        self.target_y = None
        self.current_target = self.TARGET_CC
        self.last_action = None
        self.last_pos = None
        self.stuck_counter = 0

    def Start(self, agent):
        print("Inicio del estado: GoToTarget")
        self.last_action = None
        self.last_pos = None
        self.stuck_counter = 0
        self.current_target = self.TARGET_CC
        self._update_target_indices()

    def _update_target_indices(self):
        if self.current_target == self.TARGET_EXIT:
            self.target_x = AgentConsts.EXIT_X
            self.target_y = AgentConsts.EXIT_Y
        else:
            self.target_x = AgentConsts.COMMAND_CENTER_X
            self.target_y = AgentConsts.COMMAND_CENTER_Y

    def _neighbor(self, perception, direction):
        mapping = {
            AgentConsts.MOVE_UP: AgentConsts.NEIGHBORHOOD_UP,
            AgentConsts.MOVE_DOWN: AgentConsts.NEIGHBORHOOD_DOWN,
            AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
            AgentConsts.MOVE_LEFT: AgentConsts.NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[direction]])

    def _is_hard_blocked(self, perception, direction):
        cell = self._neighbor(perception, direction)
        return cell in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE
        )

    def _is_brick(self, perception, direction):
        cell = self._neighbor(perception, direction)
        return cell in (
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _is_free(self, perception, direction):
        cell = self._neighbor(perception, direction)
        return cell not in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE,
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _is_cc(self, perception, direction):
        cell = self._neighbor(perception, direction)
        return cell == AgentConsts.COMMAND_CENTER

    def _cc_direction(self, perception):
        for direction in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_cc(perception, direction):
                return direction
        return None

    def _opposite(self, direction):
        if direction == AgentConsts.MOVE_UP:
            return AgentConsts.MOVE_DOWN
        if direction == AgentConsts.MOVE_DOWN:
            return AgentConsts.MOVE_UP
        if direction == AgentConsts.MOVE_LEFT:
            return AgentConsts.MOVE_RIGHT
        if direction == AgentConsts.MOVE_RIGHT:
            return AgentConsts.MOVE_LEFT
        return None

    def _is_player_dead(self, perception):
        return float(perception[AgentConsts.HEALTH]) <= 0

    def _is_cc_destroyed(self, perception):
      # Si el CC lasta en percepción es negativo, es que no se ve y por tanto está destruido
        cc_x = float(perception[AgentConsts.COMMAND_CENTER_X])
        cc_y = float(perception[AgentConsts.COMMAND_CENTER_Y])
        return cc_x < 0 or cc_y < 0

    def _must_go_to_exit(self, perception):
        return self._is_player_dead(perception) or self._is_cc_destroyed(perception)

    def _refresh_target(self, perception):
        if self._must_go_to_exit(perception):
            self.current_target = self.TARGET_EXIT
        else:
            self.current_target = self.TARGET_CC

        self._update_target_indices()

    def _choose_action(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        tx = float(perception[self.target_x])
        ty = float(perception[self.target_y])

        dx = tx - ax
        dy = ty - ay
        eps = 0.25

        # En este entorno: Y menor = más abajo
        dir_y = None
        dir_x = None

        if abs(dy) > eps:
            dir_y = AgentConsts.MOVE_DOWN if dy < 0 else AgentConsts.MOVE_UP

        if abs(dx) > eps:
            dir_x = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT

        if dir_x is None and dir_y is None:
            return AgentConsts.NO_MOVE, False

        if dir_x is None:
            primary = dir_y
            secondary = None
        elif dir_y is None:
            primary = dir_x
            secondary = None
        else:
            if abs(dy) >= abs(dx):
                primary, secondary = dir_y, dir_x
            else:
                primary, secondary = dir_x, dir_y

        print(
            f"[DEBUG] agent=({ax:.2f},{ay:.2f}) "
            f"target=({tx:.2f},{ty:.2f}) "
            f"type={self.current_target} "
            f"dx={dx:.2f} dy={dy:.2f} "
            f"N_UP={self._neighbor(perception, AgentConsts.MOVE_UP)} "
            f"N_DOWN={self._neighbor(perception, AgentConsts.MOVE_DOWN)} "
            f"N_RIGHT={self._neighbor(perception, AgentConsts.MOVE_RIGHT)} "
            f"N_LEFT={self._neighbor(perception, AgentConsts.MOVE_LEFT)}"
        )

        preferred = []
        if primary is not None:
            preferred.append(primary)
        if secondary is not None and secondary not in preferred:
            preferred.append(secondary)

        # 1) Intentar mover en dirección buena si está libre
        for action in preferred:
            if self._is_free(perception, action):
                return action, False

        # 2) Si la dirección buena tiene ladrillo, romperlo
        for action in preferred:
            if self._is_brick(perception, action):
                return action, True

        # 3) Probar laterales que no sean retroceso inmediato
        forbidden = set()
        if self.last_action is not None:
            forbidden.add(self._opposite(self.last_action))

        for action in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if action in preferred or action in forbidden:
                continue
            if self._is_free(perception, action):
                return action, False

        # 4) Luego probar ladrillos laterales
        for action in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if action in preferred or action in forbidden:
                continue
            if self._is_brick(perception, action):
                return action, True

        # 5) Último recurso: permitir retroceso
        for action in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_free(perception, action):
                return action, False

        for action in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_brick(perception, action):
                return action, True

        return AgentConsts.NO_MOVE, False

    def Update(self, perception, game_map, agent):
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        self._refresh_target(perception)

        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        current_pos = (ax, ay)

        action, must_shoot = self._choose_action(perception)

        # Detectar si realmente se ha quedado parado
        if self.last_pos is not None and current_pos == self.last_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        # Si lleva parado mucho, probar alternativa
        if self.stuck_counter > 6:
            for alt in (
                AgentConsts.MOVE_RIGHT,
                AgentConsts.MOVE_LEFT,
                AgentConsts.MOVE_DOWN,
                AgentConsts.MOVE_UP
            ):
                if self._is_free(perception, alt):
                    action = alt
                    must_shoot = False
                    self.stuck_counter = 0
                    break
                if self._is_brick(perception, alt):
                    action = alt
                    must_shoot = True
                    self.stuck_counter = 0
                    break

        self.last_action = action
        self.last_pos = current_pos

        shoot = can_fire and must_shoot
        print(f"[ACTION] target={self.current_target} action={action} shoot={shoot}")
        return action, shoot

    def Transit(self, perception, game_map):

        self._refresh_target(perception)

        # si el target es EXIT seguimos en este estado
        if self.current_target == self.TARGET_EXIT:
            return self.id

        cc_dir = self._cc_direction(perception)

        if cc_dir is not None:
            return "Shoot"

        return self.id

    def End(self):
        print("Fin del estado: GoToTarget")

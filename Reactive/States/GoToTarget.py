from StateMachine.State import State
from States.AgentConsts import AgentConsts


class GoToTarget(State):

    def __init__(self, id):
        super().__init__(id)
        self.target_x = None
        self.target_y = None
        self.last_action = None
        self.last_pos = None
        self.stuck_counter = 0

    def Start(self, agent):
        print("Inicio del estado: GoToTarget")
   
        self.last_action = None
        self.last_pos = None
        self.stuck_counter = 0

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

    def _choose_action(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        cx = float(perception[self.target_x])
        cy = float(perception[self.target_y])

        dx = cx - ax
        dy = cy - ay
        eps = 0.25

        # En este entorno: Y menor = más abajo
        dir_y = None
        dir_x = None

        if abs(dy) > eps:
            dir_y = AgentConsts.MOVE_DOWN if dy < 0 else AgentConsts.MOVE_UP

        if abs(dx) > eps:
            dir_x = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT

        if dir_x is None and dir_y is None:
            return AgentConsts.NOTHING, False

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
            f"[DEBUG] agent=({ax:.2f},{ay:.2f}) cc=({cx:.2f},{cy:.2f}) "
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
            if self._is_free(perception, action) and not self._is_cc(perception, action):
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
            if self._is_free(perception, action) and not self._is_cc(perception, action):
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
            if self._is_free(perception, action) and not self._is_cc(perception, action):
                return action, False

        for action in (
            AgentConsts.MOVE_UP,
            AgentConsts.MOVE_DOWN,
            AgentConsts.MOVE_RIGHT,
            AgentConsts.MOVE_LEFT
        ):
            if self._is_brick(perception, action):
                return action, True

        return AgentConsts.NOTHING, False

    def _go_attack_cc(self, perception):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])
        cx = float(perception[AgentConsts.COMMAND_CENTER_X])
        cy = float(perception[AgentConsts.COMMAND_CENTER_Y])

        dx = cx - ax
        dy = cy - ay
        eps = 0.35

        # Si ya está casi alineado en X, orientar verticalmente y disparar
        if abs(dx) <= eps:
            if dy < 0:
                return AgentConsts.MOVE_DOWN, True
            else:
                return AgentConsts.MOVE_UP, True

        # Si ya está casi alineado en Y, orientar horizontalmente y disparar
        if abs(dy) <= eps:
            if dx > 0:
                return AgentConsts.MOVE_RIGHT, True
            else:
                return AgentConsts.MOVE_LEFT, True

        # Si está en diagonal cerca del CC, primero alinearse
        if abs(dx) > abs(dy):
            if dx > 0:
                if self._is_cc(perception, AgentConsts.MOVE_RIGHT):
                    return AgentConsts.MOVE_RIGHT, True
                if self._is_free(perception, AgentConsts.MOVE_RIGHT):
                    return AgentConsts.MOVE_RIGHT, False
                if self._is_brick(perception, AgentConsts.MOVE_RIGHT):
                    return AgentConsts.MOVE_RIGHT, True
            else:
                if self._is_cc(perception, AgentConsts.MOVE_LEFT):
                    return AgentConsts.MOVE_LEFT, True
                if self._is_free(perception, AgentConsts.MOVE_LEFT):
                    return AgentConsts.MOVE_LEFT, False
                if self._is_brick(perception, AgentConsts.MOVE_LEFT):
                    return AgentConsts.MOVE_LEFT, True
        else:
            if dy < 0:
                if self._is_cc(perception, AgentConsts.MOVE_DOWN):
                    return AgentConsts.MOVE_DOWN, True
                if self._is_free(perception, AgentConsts.MOVE_DOWN):
                    return AgentConsts.MOVE_DOWN, False
                if self._is_brick(perception, AgentConsts.MOVE_DOWN):
                    return AgentConsts.MOVE_DOWN, True
            else:
                if self._is_cc(perception, AgentConsts.MOVE_UP):
                    return AgentConsts.MOVE_UP, True
                if self._is_free(perception, AgentConsts.MOVE_UP):
                    return AgentConsts.MOVE_UP, False
                if self._is_brick(perception, AgentConsts.MOVE_UP):
                    return AgentConsts.MOVE_UP, True

        return AgentConsts.NOTHING, False

    def Update(self, perception, game_map, agent):
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        ax = round(float(perception[AgentConsts.AGENT_X]), 2)
        ay = round(float(perception[AgentConsts.AGENT_Y]), 2)
        cx = round(float(perception[AgentConsts.COMMAND_CENTER_X]), 2)
        cy = round(float(perception[AgentConsts.COMMAND_CENTER_Y]), 2)

        current_pos = (ax, ay)

        # 1) Si el CC está al lado, siempre orientar hacia él y disparar cuando se pueda
        cc_dir = self._cc_direction(perception)
        if cc_dir is not None:
            self.last_action = cc_dir
            self.last_pos = current_pos
            print(f"[CC-NEAR] action={cc_dir} shoot={can_fire}")
            return cc_dir, can_fire

        # 2) Si está muy cerca del CC, usar modo especial de alineación/ataque
        if abs(cx - ax) < 3.0 and abs(cy - ay) < 3.0:
            #action, must_shoot = self._go_attack_cc(perception)
            self.last_action = action
            self.last_pos = current_pos
            shoot = can_fire and must_shoot
            print(f"[CC-ATTACK] action={action} shoot={shoot} ax={ax} ay={ay} cx={cx} cy={cy}")
            return action, shoot

        # 3) Lógica normal de navegación
        action, must_shoot = self._choose_action(perception)

        # 4) Detectar si realmente se ha quedado parado
        if self.last_pos is not None and current_pos == self.last_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        # 5) Si lleva parado mucho, probar alternativa
        if self.stuck_counter > 6:
            for alt in (
                AgentConsts.MOVE_RIGHT,
                AgentConsts.MOVE_LEFT,
                AgentConsts.MOVE_DOWN,
                AgentConsts.MOVE_UP
            ):
                if self._is_cc(perception, alt):
                    action = alt
                    must_shoot = True
                    self.stuck_counter = 0
                    break
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
        print(f"[ACTION] action={action} shoot={shoot}")
        return action, shoot

    def Transit(self, perception, game_map):
        return self.id

    def End(self):
        print("Fin del estado: GoToCommandCenter")

from StateMachine.State import State
from States.AgentConsts import AgentConsts


class AttackTarget(State):

    def __init__(self, id):
        super().__init__(id)
        self.nextState = id

    def Start(self, agent):
        print("=== INICIANDO ESTADO: ATTACK TARGET ===")
        self.nextState = self.id

        if not hasattr(agent, "direction"):
            agent.direction = AgentConsts.NEIGHBORHOOD_UP

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

    def _player_alive(self, perception):
        px = float(perception[AgentConsts.PLAYER_X])
        py = float(perception[AgentConsts.PLAYER_Y])
        return not ((px < 0 or py < 0) or (px == 0 and py == 0))

    def _cc_alive(self, perception):
        cx = float(perception[AgentConsts.COMMAND_CENTER_X])
        cy = float(perception[AgentConsts.COMMAND_CENTER_Y])
        return not ((cx < 0 or cy < 0) or (cx == 0 and cy == 0))

    def _target_in_perception(self, perception, target_value):
        if int(perception[AgentConsts.NEIGHBORHOOD_UP]) == target_value:
            return AgentConsts.MOVE_UP
        if int(perception[AgentConsts.NEIGHBORHOOD_DOWN]) == target_value:
            return AgentConsts.MOVE_DOWN
        if int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]) == target_value:
            return AgentConsts.MOVE_RIGHT
        if int(perception[AgentConsts.NEIGHBORHOOD_LEFT]) == target_value:
            return AgentConsts.MOVE_LEFT
        return None

    def _aligned_direction(self, perception, target_x, target_y):
        ax = float(perception[AgentConsts.AGENT_X])
        ay = float(perception[AgentConsts.AGENT_Y])

        dx = target_x - ax
        dy = target_y - ay
        eps = 0.35

        # misma columna
        if abs(dx) <= eps:
            if dy < 0:
                return AgentConsts.MOVE_DOWN
            if dy > 0:
                return AgentConsts.MOVE_UP

        # misma fila
        if abs(dy) <= eps:
            if dx > 0:
                return AgentConsts.MOVE_RIGHT
            if dx < 0:
                return AgentConsts.MOVE_LEFT

        return None

    def Update(self, perception, map, agent):
        self.nextState = self.id

        player_alive = self._player_alive(perception)
        cc_alive = self._cc_alive(perception)

        # Si el CC está destruido o el player está muerto -> ir al exit
        if (not cc_alive) or (not player_alive):
            print("[ATTACK] CC destruido o player muerto -> GoToExit")
            self.nextState = "GoToExit"
            return AgentConsts.NO_MOVE, False

        # PRIORIDAD: PLAYER si está vivo
        px = float(perception[AgentConsts.PLAYER_X])
        py = float(perception[AgentConsts.PLAYER_Y])

        player_dir = self._target_in_perception(perception, AgentConsts.PLAYER)

        # PLAYER en vecindad inmediata
        if player_dir is not None:
            agent.direction = self._move_to_neighborhood(player_dir)
            can_fire = bool(perception[AgentConsts.CAN_FIRE])
            print(f"[ATTACK] PLAYER inmediato -> dir={player_dir} fire={can_fire}")
            return player_dir, can_fire

        # PLAYER alineado por coordenadas
        desired_move = self._aligned_direction(perception, px, py)
        if desired_move is not None:
            agent.direction = self._move_to_neighborhood(desired_move)
            can_fire = bool(perception[AgentConsts.CAN_FIRE])
            print(f"[ATTACK] PLAYER alineado -> dir={desired_move} fire={can_fire}")
            return desired_move, can_fire

        # Si el player existe pero no está alineado, orientar hacia él
        #if player_alive:
         #   print("[ATTACK] PLAYER no alineado -> Orient")
          #  self.nextState = "Orient"
           # return AgentConsts.NO_MOVE, False

        #    print("[ATTACK] PLAYER no alineado -> Orient")
        #    self.nextState = "Orient"
        #    return AgentConsts.NO_MOVE, False


        # Si no hay player, atacar CC
        cc_dir = self._target_in_perception(perception, AgentConsts.COMMAND_CENTER)
        if cc_dir is not None:s
            agent.direction = self._move_to_neighborhood(cc_dir)
            can_fire = bool(perception[AgentConsts.CAN_FIRE])
            print(f"[ATTACK] CC inmediato -> dir={cc_dir} fire={can_fire}")
            return cc_dir, can_fire

        cx = float(perception[AgentConsts.COMMAND_CENTER_X])
        cy = float(perception[AgentConsts.COMMAND_CENTER_Y])

        desired_move = self._aligned_direction(perception, cx, cy)

        if desired_move is None:
            print("[ATTACK] CC no alineado -> Orient")
            self.nextState = "AttackTarget"
            return AgentConsts.NO_MOVE, False

        agent.direction = self._move_to_neighborhood(desired_move)
        can_fire = bool(perception[AgentConsts.CAN_FIRE])
        print(f"[ATTACK] CC alineado -> dir={desired_move} fire={can_fire}")
        return desired_move, can_fire

    def Transit(self, perception, map):
        return self.nextState

    def End(self):
        print("=== FINALIZANDO ESTADO: ATTACK TARGET ===")

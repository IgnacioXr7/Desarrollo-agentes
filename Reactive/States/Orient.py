from StateMachine.State import State
from States.AgentConsts import AgentConsts
import math


class Orient(State):

    def __init__(self, id):
        super().__init__(id)

    def _player_in_perception(self, perception):
        return (
            int(perception[AgentConsts.NEIGHBORHOOD_UP]) == AgentConsts.PLAYER or
            int(perception[AgentConsts.NEIGHBORHOOD_DOWN]) == AgentConsts.PLAYER or
            int(perception[AgentConsts.NEIGHBORHOOD_RIGHT]) == AgentConsts.PLAYER or
            int(perception[AgentConsts.NEIGHBORHOOD_LEFT]) == AgentConsts.PLAYER
        )

    def _get_target(self, perception):

        player_x = float(perception[AgentConsts.PLAYER_X])
        player_y = float(perception[AgentConsts.PLAYER_Y])
        cc_x = float(perception[AgentConsts.COMMAND_CENTER_X])
        cc_y = float(perception[AgentConsts.COMMAND_CENTER_Y])

        player_alive = player_x >= 0 and player_y >= 0
        cc_alive = cc_x >= 0 and cc_y >= 0

        # prioridad player si está en percepción
        if self._player_in_perception(perception) and player_alive:
            return player_x, player_y, "PLAYER"

        if cc_alive:
            return cc_x, cc_y, "CC"

        return None, None, None

    def Update(self, perception, map, agent):

        print("Orientándose...")

        target_x, target_y, target_name = self._get_target(perception)

        if target_x is None:
            return AgentConsts.NO_MOVE, False

        agent_x = float(perception[AgentConsts.AGENT_X])
        agent_y = float(perception[AgentConsts.AGENT_Y])

        dx = target_x - agent_x
        dy = target_y - agent_y

        # decidir hacia donde mirar
        if abs(dx) > abs(dy):
            if dx > 0:
                action = AgentConsts.MOVE_RIGHT
                agent.direction = AgentConsts.NEIGHBORHOOD_RIGHT
            else:
                action = AgentConsts.MOVE_LEFT
                agent.direction = AgentConsts.NEIGHBORHOOD_LEFT
        else:
            if dy > 0:
                action = AgentConsts.MOVE_UP
                agent.direction = AgentConsts.NEIGHBORHOOD_UP
            else:
                action = AgentConsts.MOVE_DOWN
                agent.direction = AgentConsts.NEIGHBORHOOD_DOWN

        print(f"[ORIENT] Orientado hacia {target_name} dirección {action}")

        return action, False

    def Transit(self, perception, map):
        return "AttackTarget"

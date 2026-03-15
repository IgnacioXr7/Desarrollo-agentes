from collections import deque

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

    # =========================
    # Utilidades básicas
    # =========================

    def _neighbor(self, perception, move):
        mapping = {
            AgentConsts.MOVE_UP: AgentConsts.NEIGHBORHOOD_UP,
            AgentConsts.MOVE_DOWN: AgentConsts.NEIGHBORHOOD_DOWN,
            AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
            AgentConsts.MOVE_LEFT: AgentConsts.NEIGHBORHOOD_LEFT,
        }
        return int(perception[mapping[move]])

    def _is_hard_value(self, cell):
        return cell in (
            AgentConsts.UNBREAKABLE,
            AgentConsts.SEMI_UNBREKABLE
        )

    def _is_brick_value(self, cell):
        return cell in (
            AgentConsts.BRICK,
            AgentConsts.SEMI_BREKABLE
        )

    def _is_free_value(self, cell):
        return not self._is_hard_value(cell) and not self._is_brick_value(cell)

    def _is_hard_blocked(self, perception, move):
        return self._is_hard_value(self._neighbor(perception, move))

    def _is_brick(self, perception, move):
        return self._is_brick_value(self._neighbor(perception, move))

    def _next_pos(self, x, y, move):
        if move == AgentConsts.MOVE_UP:
            return x, y + 1
        if move == AgentConsts.MOVE_DOWN:
            return x, y - 1
        if move == AgentConsts.MOVE_RIGHT:
            return x + 1, y
        if move == AgentConsts.MOVE_LEFT:
            return x - 1, y
        return x, y

    def _at_exit_zone(self, perception):
        ax = round(float(perception[AgentConsts.AGENT_X]))
        ay = round(float(perception[AgentConsts.AGENT_Y]))
        ex = round(float(perception[AgentConsts.EXIT_X]))
        ey = round(float(perception[AgentConsts.EXIT_Y]))

        return ax == ex and ay == ey

    def _is_looping(self):
        if len(self.pos_history) < 4:
            return False
        a, b, c, d = self.pos_history[-4:]
        return a == c and b == d and a != b

    # =========================
    # Utilidades del mapa
    # =========================

    def _map_dims(self, game_map):
        height = len(game_map)
        width = len(game_map[0]) if height > 0 else 0
        return width, height

    def _in_bounds(self, game_map, x, y):
        width, height = self._map_dims(game_map)
        return 0 <= x < width and 0 <= y < height

    def _cell(self, game_map, x, y):
        # Si tu mapa está invertido en Y, aquí es donde tendrías que corregirlo
        return int(game_map[y][x])

    def _neighbors4(self, x, y):
        return [
            (x, y + 1, AgentConsts.MOVE_UP),
            (x, y - 1, AgentConsts.MOVE_DOWN),
            (x + 1, y, AgentConsts.MOVE_RIGHT),
            (x - 1, y, AgentConsts.MOVE_LEFT),
        ]

    # =========================
    # BFS exacto al exit
    # =========================

    def _bfs_path(self, game_map, start, goal, allow_bricks):
        """
        Devuelve una lista de acciones hasta goal:
        [MOVE_..., MOVE_..., ...]
        Si no hay camino, devuelve [].
        """
        sx, sy = start
        gx, gy = goal

        if not self._in_bounds(game_map, sx, sy):
            return []
        if not self._in_bounds(game_map, gx, gy):
            return []

        q = deque()
        q.append((sx, sy))

        visited = {(sx, sy)}
        parent = {(sx, sy): None}
        parent_move = {}

        while q:
            x, y = q.popleft()

            if (x, y) == (gx, gy):
                break

            for nx, ny, move in self._neighbors4(x, y):
                if not self._in_bounds(game_map, nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue

                cell = self._cell(game_map, nx, ny)

                if self._is_hard_value(cell):
                    continue

                if self._is_brick_value(cell) and not allow_bricks:
                    continue

                visited.add((nx, ny))
                parent[(nx, ny)] = (x, y)
                parent_move[(nx, ny)] = move
                q.append((nx, ny))

        if (gx, gy) not in parent:
            return []

        path = []
        node = (gx, gy)
        while parent[node] is not None:
            path.append(parent_move[node])
            node = parent[node]
        path.reverse()
        return path

    def _choose_action(self, perception, game_map):
        if self._at_exit_zone(perception):
            return AgentConsts.NO_MOVE, False

        ax = round(float(perception[AgentConsts.AGENT_X]))
        ay = round(float(perception[AgentConsts.AGENT_Y]))
        ex = round(float(perception[AgentConsts.EXIT_X]))
        ey = round(float(perception[AgentConsts.EXIT_Y]))

        start = (ax, ay)
        goal = (ex, ey)

        # 1) Intentar primero sin atravesar ladrillos
        path = self._bfs_path(game_map, start, goal, allow_bricks=False)

        # 2) Si no hay camino, permitir ladrillos
        if not path:
            path = self._bfs_path(game_map, start, goal, allow_bricks=True)

        if not path:
            return AgentConsts.NO_MOVE, False

        move = path[0]

        # Si el primer paso es ladrillo, disparar
        if self._is_brick(perception, move):
            return move, True

        # Si el primer paso está libre, moverse
        if not self._is_hard_blocked(perception, move):
            return move, False

        return AgentConsts.NO_MOVE, False

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

        action, must_shoot = self._choose_action(perception, game_map)

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
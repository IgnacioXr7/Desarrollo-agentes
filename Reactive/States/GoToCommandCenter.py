from States.AgentConsts import AgentConsts
from StateMachine.State import State
from collections import deque


class GoToCommandCenter(State):
    """
    Navega hacia la Command Center por el camino más corto.

    Estrategia:
      1. BFS sobre el mapa para hallar la dirección óptima (ignora ladrillos,
         los trata como traversables porque se pueden destruir).
      2. Si la dirección elegida tiene un ladrillo, dispara para abrirlo.
      3. Si hay un shell viniendo hacia nosotros y podemos disparar, lo
         interceptamos (disparamos en esa dirección).
      4. Fallback greedy si el mapa no está disponible.
    """

    # ------------------------------------------------------------------
    # Constantes internas
    # ------------------------------------------------------------------
    # El mapa lógico es 26x26 (cada casilla "grande" son 2x2 casillas lógicas)
    # pero las coordenadas de percepción están en el espacio de 13x13 (0-12).
    # Usamos el mapa tal como llega (15x15 o el tamaño real).
    DIRS = [
        (AgentConsts.MOVE_UP,    0, -1),
        (AgentConsts.MOVE_DOWN,  0,  1),
        (AgentConsts.MOVE_LEFT, -1,  0),
        (AgentConsts.MOVE_RIGHT, 1,  0),
    ]

    def __init__(self, id):
        super().__init__(id)
        self._cached_path_dir = None   # dirección BFS cacheada
        self._last_agent_pos  = None   # para invalidar caché si nos movimos
        self._stuck_counter   = 0      # turnos sin movernos

    # ------------------------------------------------------------------
    # Arranque / fin
    # ------------------------------------------------------------------
    def Start(self, agent):
        print("Inicio del estado: GoToCommandCenter")
        self._cached_path_dir = None
        self._last_agent_pos  = None
        self._stuck_counter   = 0

    def End(self):
        print("Fin del estado: GoToCommandCenter")

    # ------------------------------------------------------------------
    # Helpers de percepción
    # ------------------------------------------------------------------
    _NEIGH_IDX = {
        AgentConsts.MOVE_UP:   AgentConsts.NEIGHBORHOOD_UP,
        AgentConsts.MOVE_DOWN:  AgentConsts.NEIGHBORHOOD_DOWN,
        AgentConsts.MOVE_RIGHT: AgentConsts.NEIGHBORHOOD_RIGHT,
        AgentConsts.MOVE_LEFT:  AgentConsts.NEIGHBORHOOD_LEFT,
    }

    def _neighbor_type(self, perception, direction):
        return int(perception[self._NEIGH_IDX[direction]])

    def _is_hard_blocked(self, perception, direction):
        """UNBREAKABLE bloquea el movimiento; BRICK se puede abrir a tiros."""
        return self._neighbor_type(perception, direction) == AgentConsts.UNBREAKABLE

    def _is_brick(self, perception, direction):
        return self._neighbor_type(perception, direction) == AgentConsts.BRICK

    # ------------------------------------------------------------------
    # BFS en el mapa
    # ------------------------------------------------------------------
    def _bfs_direction(self, map, start, goal):
        """
        BFS desde start=(col,row) hasta goal=(col,row).
        Tratamos UNBREAKABLE como muro infranqueable.
        BRICK cuenta como traversable (lo destruimos de camino).
        Devuelve la acción (MOVE_*) del primer paso, o None si no hay camino.
        """
        if map is None:
            return None

        rows = len(map)
        cols = len(map[0]) if rows > 0 else 0
        if rows == 0 or cols == 0:
            return None

        sx, sy = int(round(start[0])), int(round(start[1]))
        gx, gy = int(round(goal[0])), int(round(goal[1]))

        # Clamp al rango válido
        sx = max(0, min(sx, cols - 1))
        sy = max(0, min(sy, rows - 1))
        gx = max(0, min(gx, cols - 1))
        gy = max(0, min(gy, rows - 1))

        if (sx, sy) == (gx, gy):
            return None  # ya estamos ahí

        visited = [[False] * cols for _ in range(rows)]
        visited[sy][sx] = True
        # queue: (x, y, first_action)
        queue = deque()

        for action, ddx, ddy in self.DIRS:
            nx, ny = sx + ddx, sy + ddy
            if 0 <= nx < cols and 0 <= ny < rows and not visited[ny][nx]:
                cell = int(map[ny][nx])
                if cell != AgentConsts.UNBREAKABLE and cell != AgentConsts.SEMI_UNBREKABLE:
                    visited[ny][nx] = True
                    queue.append((nx, ny, action))

        while queue:
            x, y, first_action = queue.popleft()
            if x == gx and y == gy:
                return first_action
            for action, ddx, ddy in self.DIRS:
                nx, ny = x + ddx, y + ddy
                if 0 <= nx < cols and 0 <= ny < rows and not visited[ny][nx]:
                    cell = int(map[ny][nx])
                    if cell != AgentConsts.UNBREAKABLE and cell != AgentConsts.SEMI_UNBREKABLE:
                        visited[ny][nx] = True
                        queue.append((nx, ny, first_action))

        return None  # sin camino

    # ------------------------------------------------------------------
    # Fallback greedy (sin mapa)
    # ------------------------------------------------------------------
    def _greedy_direction(self, perception):
        """
        Elige la dirección más prometedora basándose solo en coordenadas
        y en la percepción inmediata de vecinos.
        """
        ax = perception[AgentConsts.AGENT_X]
        ay = perception[AgentConsts.AGENT_Y]
        cx = perception[AgentConsts.COMMAND_CENTER_X]
        cy = perception[AgentConsts.COMMAND_CENTER_Y]

        dx = cx - ax   # positivo → CC a la derecha
        dy = cy - ay   # positivo → CC abajo (Y crece hacia abajo)

        if abs(dx) >= abs(dy):
            primary   = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
            secondary = AgentConsts.MOVE_DOWN  if dy > 0 else AgentConsts.MOVE_UP
        else:
            primary   = AgentConsts.MOVE_DOWN  if dy > 0 else AgentConsts.MOVE_UP
            secondary = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT

        # Añadir los otros dos ejes como últimos recursos
        candidates = [primary, secondary]
        for d in (AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN, AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT):
            if d not in candidates:
                candidates.append(d)

        for action in candidates:
            if not self._is_hard_blocked(perception, action):
                return action

        return AgentConsts.DO_NOTHING  # completamente rodeado de indestructibles

    # ------------------------------------------------------------------
    # Update principal
    # ------------------------------------------------------------------
    def Update(self, perception, map, agent):
        ax = perception[AgentConsts.AGENT_X]
        ay = perception[AgentConsts.AGENT_Y]
        cx = perception[AgentConsts.COMMAND_CENTER_X]
        cy = perception[AgentConsts.COMMAND_CENTER_Y]
        can_fire = bool(perception[AgentConsts.CAN_FIRE])

        # ---- 1. Detectar shell entrante → interceptar ----
        shell_action, shoot = self._intercept_shell(perception, can_fire)
        if shell_action is not None:
            return shell_action, shoot

        # ---- 2. Calcular dirección hacia CC ----
        current_pos = (ax, ay)

        # Invalidar caché si nos hemos movido
        if self._last_agent_pos != current_pos:
            self._cached_path_dir = None
            self._last_agent_pos  = current_pos
            self._stuck_counter   = 0
        else:
            self._stuck_counter += 1

        # BFS con mapa si disponible
        action = self._bfs_direction(map, (ax, ay), (cx, cy))

        # Fallback greedy
        if action is None:
            action = self._greedy_direction(perception)

        # Si llevamos muchos turnos parados, forzar dirección diferente
        if self._stuck_counter > 5:
            action = self._unstuck(perception, action)
            self._stuck_counter = 0

        # ---- 3. Decidir disparo ----
        shoot = False
        if action != AgentConsts.DO_NOTHING:
            neighbor = self._neighbor_type(perception, action)
            if neighbor == AgentConsts.BRICK and can_fire:
                # Hay ladrillo bloqueando → disparar para abrirlo
                shoot = True
            elif neighbor == AgentConsts.PLAYER and can_fire:
                # Bonus: si el jugador está justo delante, disparar
                shoot = True

        return action, shoot

    # ------------------------------------------------------------------
    # Interceptar shell entrante
    # ------------------------------------------------------------------
    def _intercept_shell(self, perception, can_fire):
        """
        Si hay un shell en alguna dirección adyacente y podemos disparar,
        giramos hacia él y disparamos.
        Devuelve (accion, shoot) o (None, False) si no hay shell.
        """
        for action in (AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN, AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT):
            if self._neighbor_type(perception, action) == AgentConsts.SHELL:
                if can_fire:
                    return action, True
                else:
                    # No podemos disparar → intentar esquivar (perpendicular)
                    perp = self._perpendicular(action)
                    for p in perp:
                        if not self._is_hard_blocked(perception, p):
                            return p, False
        return None, False

    def _perpendicular(self, action):
        """Devuelve las dos direcciones perpendiculares a 'action'."""
        if action in (AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN):
            return [AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT]
        return [AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN]

    # ------------------------------------------------------------------
    # Desatascarse
    # ------------------------------------------------------------------
    def _unstuck(self, perception, preferred):
        """
        Si llevamos muchos ticks sin movernos, intentar una dirección
        distinta a la preferida.
        """
        for action in (AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN, AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT):
            if action != preferred and not self._is_hard_blocked(perception, action):
                return action
        return preferred

    # ------------------------------------------------------------------
    # Transición (estado único por ahora)
    # ------------------------------------------------------------------
    def Transit(self, perception, map):
        return self.id
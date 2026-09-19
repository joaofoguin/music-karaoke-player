from models.track import Track


class QueueManager:
    def __init__(self):
        self.tracks = []
        self.current_index = -1

    def add(self, track: Track):
        self.tracks.append(track)

        # Se for a primeira música adicionada,
        # ela passa a ser a música atual.
        if self.current_index == -1:
            self.current_index = 0

    def remove(self, index: int):
        if not 0 <= index < len(self.tracks):
            return None

        removed = self.tracks.pop(index)

        if not self.tracks:
            self.current_index = -1
            return removed

        if index < self.current_index:
            self.current_index -= 1

        elif index == self.current_index:
            if self.current_index >= len(self.tracks):
                self.current_index = len(self.tracks) - 1

        return removed

    def clear(self):
        self.tracks.clear()
        self.current_index = -1

    def move(self, index: int, destination: int):
        """Move a track while keeping the current-track reference consistent."""
        if not (
            0 <= index < len(self.tracks)
            and 0 <= destination < len(self.tracks)
            and index != destination
        ):
            return False

        track = self.tracks.pop(index)
        self.tracks.insert(destination, track)

        if index == self.current_index:
            self.current_index = destination
        elif index < self.current_index <= destination:
            self.current_index -= 1
        elif destination <= self.current_index < index:
            self.current_index += 1

        return True

    def set_play_next(self, index: int) -> bool:
        """Move a faixa especificada para ser a próxima a tocar (logo após a faixa atual)."""
        if not (0 <= index < len(self.tracks)):
            return False

        if self.current_index == -1:
            return self.move(index, 0)

        if index == self.current_index:
            return False

        # Se o item já for o próximo, não precisa mover
        if index == self.current_index + 1:
            return True

        destino = self.current_index + 1 if index > self.current_index else self.current_index
        return self.move(index, destino)

    def current(self):
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]

        return None

    def set_current(self, index: int):
        if 0 <= index < len(self.tracks):
            self.current_index = index
            return self.tracks[index]

        return None

    def previous(self):
        if not self.tracks:
            return None

        if self.current_index > 0:
            self.current_index -= 1
            return self.tracks[self.current_index]

        return None

    def next(self):
        if not self.tracks:
            return None

        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
            return self.tracks[self.current_index]

        return None

from abc import ABC, abstractmethod


class ClientInstaller(ABC):
    """
    Writes/restores one IDE client's config so it points at LAIR
    (I-14). Every concrete installer must back up before writing and
    be able to undo itself from that backup -- config LAIR didn't
    write is the user's, and must always be recoverable.
    """

    name: str

    @abstractmethod
    def detect(self) -> bool:
        """
        Best-effort check for whether this client appears to be
        installed on this machine (e.g. its config directory exists).
        Never raises -- a detection failure means "not detected", not
        a crash.
        """

        raise NotImplementedError

    @abstractmethod
    def install(self, base_url: str) -> str:
        """
        Point this client at `base_url`, backing up any existing
        config first. Returns a human-readable summary line.
        """

        raise NotImplementedError

    @abstractmethod
    def uninstall(self) -> str:
        """
        Restore this client's config from the backup `install()` made.
        Returns a human-readable summary line.
        """

        raise NotImplementedError

class PlexConnectionError(Exception):
    """
    Unable to connect to Plex server
    """
    pass


class PlexAPIKeyNotFound(Exception):
    pass


class PlexLibraryUndefinedType(Exception):
    pass


class PlexMissingVideoKey(Exception):
    pass

class PlexMissingSeasonKey(Exception):
    pass
class AoASDKError(Exception):
    pass


class RepoNotFound(AoASDKError):
    pass


class SurfaceNotFound(AoASDKError):
    pass


class RecordNotFound(SurfaceNotFound):
    pass


class SkillNotFound(SurfaceNotFound):
    pass


class UnknownKind(SurfaceNotFound):
    pass


class IncompatibleSurfaceVersion(AoASDKError):
    pass


class InvalidSurface(AoASDKError):
    pass

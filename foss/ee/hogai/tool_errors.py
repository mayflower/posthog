class MaxToolError(Exception):
    pass


class MaxToolRetryableError(MaxToolError):
    pass


class MaxToolFatalError(MaxToolError):
    pass


class MaxToolAccessDeniedError(MaxToolError):
    pass

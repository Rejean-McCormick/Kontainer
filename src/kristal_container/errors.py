"""Stable error codes; never put credentials into diagnostic messages."""


class ContainerError(Exception):
    code = "container-error"


class FormatError(ContainerError):
    code = "invalid-format"


class IntegrityError(ContainerError):
    code = "integrity-failed"


class AccessError(ContainerError):
    code = "access-denied"


class PolicyError(ContainerError):
    code = "policy-denied"


class LimitError(ContainerError):
    code = "limit-exceeded"


class UnsupportedError(ContainerError):
    code = "unsupported-profile"

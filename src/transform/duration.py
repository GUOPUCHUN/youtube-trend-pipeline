"""Parse ISO 8601 duration strings from the YouTube API.

The API returns contentDetails.duration in ISO 8601 format, e.g. "PT4M13S".
Downstream analysis needs an integer number of seconds.

Only the time component (hours/minutes/seconds) is supported. YouTube never
returns date components (years/months/days) for video durations, so a value
containing them is treated as unexpected input rather than silently ignored.
"""

import re

# PT[nH][nM][nS] — every component is optional, but at least one must exist.
_ISO8601_TIME = re.compile(
    r"^PT"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?$"
)


class DurationParseError(ValueError):
    """Raised when a duration string does not match the expected format."""


def parse_duration(value: str) -> int:
    """Convert an ISO 8601 duration to a number of seconds.

    >>> parse_duration("PT4M13S")
    253
    >>> parse_duration("PT1H")
    3600

    Raises:
        DurationParseError: if the string is empty, malformed, or contains
            no time components at all (e.g. bare "PT").
    """
    if not value:
        raise DurationParseError("duration is empty")

    match = _ISO8601_TIME.match(value)
    if match is None:
        raise DurationParseError(f"unparseable duration: {value!r}")

    parts = match.groupdict()
    if all(v is None for v in parts.values()):
        # "PT" alone matches the regex but carries no information.
        raise DurationParseError(f"duration has no components: {value!r}")

    hours = int(parts["hours"] or 0)
    minutes = int(parts["minutes"] or 0)
    seconds = int(parts["seconds"] or 0)

    return hours * 3600 + minutes * 60 + seconds

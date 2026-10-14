"""Builds a SimConfig from the settings file (NFR-C1 to NFR-C4, NFR-U1)."""

from typing import TextIO

from elevator.config.sim_config import CarSpec, SimConfig, Strategy, TrafficMode

# Default floor count.
DEFAULT_FLOORS = 50
# Default number of cars, all regular.
DEFAULT_CARS = 6
# Default capacity for each car (FR-CAR-1).
DEFAULT_CAPACITY = 10


class ConfigLoader:
    """Builds a SimConfig from the settings file (NFR-C1 to NFR-C4, NFR-U1).

    Settings file format is standard key=value lines. Car numbers start at 1:

        requests=requests.csv
        strategy=COST_BASED
        mode=NORMAL
        floors=50
        cars=6
        capacity=10
        startFloor.1=1
        parkingFloor.6=1
        express.6=1,5,10,20

    requests, strategy, and mode are required. Any other key that is missing takes its default, except
    parkingFloor.N for every car in LUNCH_OUT_RUSH and EVENING_RUSH, which must be set (FR-TRF-4).
    """

    @staticmethod
    def load(settings: TextIO) -> SimConfig:
        """Reads the settings text and builds the config. The caller opens the file or resource.

        Args:
            settings: the settings text, in key=value form.

        Returns:
            the validated config.

        Raises:
            ValueError: if a required setting is missing or a value is not valid.
        """
        props = ConfigLoader.read_properties(settings)
        return ConfigLoader.build(props)

    @staticmethod
    def build(props: dict[str, str]) -> SimConfig:
        """Builds the config from already-loaded settings, applying defaults for missing keys.

        Args:
            props: the settings, as a dict of key to text value.

        Returns:
            the validated config.

        Raises:
            ValueError: if a required key is missing, or a value is not valid (NFR-C2 to NFR-C4).
        """
        requests = ConfigLoader._required(props, "requests")
        strategy = ConfigLoader._parse_enum(props, "strategy", Strategy)
        mode = ConfigLoader._parse_enum(props, "mode", TrafficMode)
        floors = ConfigLoader._get_int(props, "floors", DEFAULT_FLOORS)
        car_count = ConfigLoader._get_int(props, "cars", DEFAULT_CARS)
        default_capacity = ConfigLoader._get_int(props, "capacity", DEFAULT_CAPACITY)

        # FR-TRF-4: in these modes every car must have its own parking floor, so the default is not allowed.
        parking_required = mode in (TrafficMode.LUNCH_OUT_RUSH, TrafficMode.EVENING_RUSH)

        # Read each car's settings in car-number order, starting at car 1.
        cars = []
        for number in range(1, car_count + 1):
            capacity = ConfigLoader._get_int(props, f"capacity.{number}", default_capacity)
            start_floor = ConfigLoader._get_int(props, f"startFloor.{number}", 1)
            parking_key = f"parkingFloor.{number}"
            if parking_required and parking_key not in props:
                raise ValueError(f"setting '{parking_key}' is required in {mode.value} mode (FR-TRF-4)")
            parking_floor = ConfigLoader._get_int(props, parking_key, 1)
            served = ConfigLoader._parse_served_floors(props.get(f"express.{number}"))
            cars.append(CarSpec(capacity, start_floor, parking_floor, served))
        return SimConfig(floors, cars, strategy, mode, requests)

    @staticmethod
    def read_properties(settings: TextIO) -> dict[str, str]:
        """Reads key=value lines into a dict. Blank lines and lines starting with # are skipped.

        Args:
            settings: the settings text.

        Returns:
            the settings, with keys and values trimmed.
        """
        props = {}
        for raw_line in settings.read().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # Split on the first "=" only, so values may contain "=".
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
        return props

    @staticmethod
    def _required(props: dict[str, str], key: str) -> str:
        """Reads a setting that must be present.

        Args:
            props: the settings.
            key: the key to read.

        Returns:
            the trimmed value.

        Raises:
            ValueError: if the key is missing or empty.
        """
        value = props.get(key)
        if value is None or not value.strip():
            raise ValueError(f"setting '{key}' is required in the settings file")
        return value.strip()

    @staticmethod
    def _parse_enum(props: dict[str, str], key: str, enum_type: type) -> object:
        """Reads a required enum setting, such as strategy or mode. Case does not matter.

        Args:
            props: the settings.
            key: the key to read.
            enum_type: the enum class to look the value up in.

        Returns:
            the enum member.

        Raises:
            ValueError: if the value is not one of the enum names.
        """
        value = ConfigLoader._required(props, key)
        try:
            return enum_type[value.upper()]
        except KeyError:
            raise ValueError(f"setting '{key}' has unknown value '{value}'") from None

    @staticmethod
    def _get_int(props: dict[str, str], key: str, default_value: int) -> int:
        """Reads an integer setting, or returns the default when the key is missing.

        Args:
            props: the settings.
            key: the key to read.
            default_value: value to use when the key is missing.

        Returns:
            the parsed integer.

        Raises:
            ValueError: if the value is not an integer.
        """
        value = props.get(key)
        if value is None:
            return default_value
        try:
            return int(value.strip())
        except ValueError:
            raise ValueError(f"{key} must be a whole number, got '{value}'") from None

    @staticmethod
    def _parse_served_floors(value: str | None) -> set[int] | None:
        """Parses an express car's served floors, such as "1,5,10,20". Returns None for a regular car.

        Args:
            value: the comma-separated list, or None if the key is absent.

        Returns:
            the served set, or None for a regular car (FR-CAR-3).

        Raises:
            ValueError: if an entry is not a whole number.
        """
        if value is None:
            return None
        floors = set()
        for part in value.split(","):
            try:
                floors.add(int(part.strip()))
            except ValueError:
                raise ValueError(f"express floors must be whole numbers, got '{part.strip()}'") from None
        return floors

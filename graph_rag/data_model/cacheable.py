from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Type, TypeVar, Any, get_args, get_origin, Union

T = TypeVar('T', bound='Cacheable')


@dataclass
class Cacheable(ABC):

    def to_dict(self) -> dict[str, Any]:
        data = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Enum):
                data[field.name] = value.name
            elif isinstance(value, list) and is_dataclass(get_args(field.type)[0]) and issubclass(
                    get_args(field.type)[0], Cacheable):
                data[field.name] = [item.to_dict() for item in value]
            elif is_dataclass(field.type) and issubclass(field.type, Cacheable):
                data[field.name] = value.to_dict() if value is not None else None
            else:
                data[field.name] = value
        data['version'] = self.get_class_version()
        return data

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        if data['version'] != cls.get_class_version():
            raise ValueError(f"Model version mismatch: expected {cls.get_class_version()}, got {data['version']}")

        init_args: dict[str, Any] = {}
        for field in fields(cls):
            field_type = field.type
            if field.name not in data:
                continue
            value = data[field.name]

            # Handle Optional types
            if get_origin(field_type) is Union and type(None) in get_args(field_type):
                field_type = next(arg for arg in get_args(field_type) if arg is not type(None))

            if get_origin(field_type) is list:
                item_type = get_args(field_type)[0]
                if is_dataclass(item_type) and issubclass(item_type, Cacheable):
                    init_args[field.name] = [item_type.from_dict(item) for item in value]
                else:
                    init_args[field.name] = value
            elif is_dataclass(field_type) and issubclass(field_type, Cacheable):
                init_args[field.name] = field_type.from_dict(value)
            elif issubclass(field_type, Enum):
                init_args[field.name] = field_type[value]
            else:
                init_args[field.name] = value

        return cls(**init_args)

    @classmethod
    @abstractmethod
    def get_class_version(cls) -> int: ...

    @classmethod
    def check_version(cls: Type[T], data_version: int):
        if data_version != cls.get_class_version():
            raise ValueError(f"Model version mismatch: expected {cls.get_class_version()}, got {data_version}")
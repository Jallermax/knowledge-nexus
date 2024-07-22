from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, fields
from enum import Enum
from typing import Type, TypeVar, Dict, Any, get_args, get_origin, Union

T = TypeVar('T', bound='Cacheable')


@dataclass
class Cacheable(ABC):

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['version'] = self.get_class_version()
        # Convert enums to their values
        for field in fields(self):
            if isinstance(data[field.name], Enum):
                data[field.name] = data[field.name].name
        return data

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        if data['version'] != cls.get_class_version():
            raise ValueError(f"Model version mismatch: expected {cls.get_class_version()}, got {data['version']}")
        # Convert string representations back to enums
        init_args: Dict[str, Any] = {}
        for field in fields(cls):
            field_type = field.type
            if get_origin(field_type) is Union:
                # Extract the actual type from Optional or Union
                field_type = next(t for t in get_args(field_type) if t is not type(None))
            value = data[field.name]
            if issubclass(field_type, Enum):
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

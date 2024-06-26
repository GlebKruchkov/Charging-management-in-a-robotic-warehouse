import typing
import simpy
import simpy.resources.store
import simpy.resources.resource

from exceptions import (
    NotFreeCellException,
    NotInputCellException,
    CellIsReservedException,
    UnknownRequestException
)

if typing.TYPE_CHECKING:
    from structures import Position

MailInputGetter = typing.Callable[
    [int],
    typing.Callable[[], simpy.resources.store.StoreGet]]


class Cell:
    @property
    def free(self):
        return self._free

    @property
    def input_id(self):
        return self._input_id

    @property
    def output_id(self):
        return self._output_id

    @property
    def charge_id(self):
        return self._charge_id

    @property
    def reserved(self):
        return self._reserved

    @typing.overload
    def __init__(self, env: simpy.Environment,
                 get_mail_input: None = None,
                 input_id: None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True) -> None:
        ...

    @typing.overload
    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter,
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True) -> None:
        ...

    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter | None = None,
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True):
        self._env = env
        self._free = free
        self._input_id = input_id
        if input_id is not None:
            if get_mail_input is None:
                raise TypeError("No get_mail_input")
            self._input = get_mail_input(input_id)
        else:
            self._input = None
        self._output_id = output_id
        self._charge_id = charge_id
        self._reserved = False
        self._requests: list[simpy.Event] = []
        self.position: None | Position = None

    def reserve(self) -> simpy.Event:
        if not self._free:
            raise NotFreeCellException(self)
        if self._reserved:
            raise CellIsReservedException(self)
        self._requests.append(self._env.timeout(0))
        self._reserved = True
        return self._requests[-1]

    def unreserve(self, request: simpy.Event) -> None:
        if request != self._requests[-1]:
            raise UnknownRequestException(f"{self} got unknown request.")
        self._requests.pop()
        self._reserved = False

    def get_input(self):
        if self._input is None:
            raise NotInputCellException(self)
        return self._input()

    @typing.override
    def __repr__(self):
        return f"Cell{self.position}"


class SafeCell(Cell, simpy.Resource):
    """
    Cell for `SafeRobot` so robot waits for cell to free
    """

    @typing.overload
    def __init__(self, env: simpy.Environment,
                 get_mail_input: None = None,
                 input_id: None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True) -> None:
        ...

    @typing.overload
    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter,
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True) -> None:
        ...

    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter | None = None,
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None,
                 free: bool = True):
        simpy.Resource.__init__(self, env)
        Cell.__init__(self, env, get_mail_input, input_id, output_id, charge_id, free)  # type: ignore

    @typing.override
    def reserve(self) -> simpy.Event:
        if not self._free:
            raise NotFreeCellException(self)
        return simpy.Resource.request(self)

    @typing.override
    def unreserve(self, request: simpy.Event):
        if isinstance(request, simpy.resources.resource.Request):
            request.cancel()
            self.release(request)
        else:
            print("unreserved")

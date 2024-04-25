# Charging-management-in-a-robotic-warehouse

# Моделирование роботизированного сортировочного центра. Управление зарядками для роя логистических роботов.

## Основные предположения

В пункты получения сортировочного логистического центра непрерывно поступают посылки, которые роботы должны сортировать - развести в соответствующие пункты назначения центра.

Сортировочный центр - прямоугольная площадка, разделённая на клетки, некоторые из которых помечены, как пункты получения и назначения для посылок, пункты зарядных устройств для роботов.

Роботы могут двигаться вперед и поворачиваться в одном из 4 направлений. Роботы выполняют действия по командам системы управления за различные, заданные моделью, дискретные времена:
- бездействие (время задается системой управления)
- движение на одну клетку вперед
- поворот на 90 градусов
- взятие посылки (в пункте получения)
- сдача посылки (в пункте назначения)
- зарядка (в пункте с зарядным устройством)

В момент получения посылки роботом, случайным образом выбирается её пункт назначения - куда нужно отвести.

У всех роботов на складе установлен минимальный порог заряда. Если робот без письма и уровень его заряда меньше либо равен пороговому, то робот едет заряжаться в пункт, который потенциально должны были освободить первым.

Столкновением роботов считается одновременное использование одной клетки двумя роботами:
- находятся в одной клетке
- движутся в одну клетку
- один движется в клетку, в которой находится другой
- один движется в клетку, откуда движется другой

## Установка
1. предполагается, что уже установлены:
    - python 3.12
    - [simpy](https://github.com/esemble/simpy) (библиотека python)

## Конфигурация модели

Конфигурация задается несколькими `.json` файлами и выбранным алгоритмом. Запуск производится из консоли.

### Карта склада
Конфигурация склада задается файлом `.json`, который содержит:
- `span` - расстояние между клетками
- `cells` - прямоугольный двумерный массив клеток (1 координата - строка сверху вниз, 2 координата - столбец слева направо), каждая из которых содержит необязательные:
    - `free` - может ли робот находиться, по умолчанию может: `true`
    - `inputId` - уникальный номер пункта получения, по умолчанию его нет
    - `outputId` - уникальный номер пункта назначения, по умолчанию его нет
    - `chargeId` - уникальный номер пункта c зарядным устройством, по умолчанию его нет


### Свойства роботов
Робот создаётся со следующими параметрами:
- `timeToMove` - время для движения вперед на 1 клетку
- `timeToTurn`- время для поворота на 90 градусов
- `timeToTake`  - время, чтобы взять посылку
- `timeToPut` - время, чтобы положить посылку
- `timeToCharge` - время, чтобы зарядиться на 100%
- `charge_to_turn` - заряд, который робот тратит, чтобы повернуться
- `charge_to_go` - заряд, который робот тратит, чтобы пройти одну клетку вперёд
- `charge_to_take` - заряд, который робот тратит, чтобы взять посылку
- `charge_to_put` - заряд, который робот тратит, чтобы положить посылку
- `charge_to_stop` - заряд, который робот тратит, чтобы остановиться
- `charge_to_start` - заряд, который робот тратит, чтобы начать движение


### Расположение роботов
В модели также задаётся начальное расположение роботов на складе. Параметры, которые заданы:
- `robots` - список, элементы которого содержат:
    - `id` - необязательный id
    - `x` - позиция по 1 координате, считая с 0
    - `y` - позиция по 2 координате, считая с 0
    - `direction` - направление одно из:
        - `up` - вверх
        - `left` - влево
        - `down` - вниз
        - `right` - вправо

## Архитектура моделирования

Модель разделена на 2 части: сменная система управления и модель (управляемого) склада.

До запуска, модель склада:
1. считывает файлы конфигурации,
2. расставляет роботов и уведомляет о каждом систему управления,
3. запрашивает у системы управления первое действие для каждого робота,

Во время исполнения, модель повторяет следующее:
1. проверяет возможность выполнения полученного действия робота.
2. если возможно, выполняет действие робота
3. если действие не может быть выполнено, возникает ошибка или оповещается система управление в зависимости от вида ошибки,
4. когда действие закончилось, запрашивает следующее действие у системы управления,

Когда моделирование закончено, то есть прошло заданное время или доставлено заданное количество посылок, модель склада выводит требуемые результаты.

### Модель управляемого склада

#### Конструкция модели склада
- [/brains/](/brains/) - алгоритмы управления
- [/mail_factories/](/mail_factories/) - генераторы посылок
- [/maps/](/mail_factories/) - карты, основная и дополнительные которые хранят дополнительную информацию
- [/mail_factories/](/mail_factories/) - генераторы посылок  для пунктов получения.
- [/structures.py](/structures.py) - неизменяемые структуры данных
- [/modelling.py](/modelling.py) - основной класс `Model`, связывающий остальные классы и получающий управление после получения команды моделирования.
- [/brains/brain.py](/brains/brain.py) - абстрактный класс `Brain`, описывающий интерфейс системы управления.
- [/maps/map.py](/maps/map.py) - карта склада `Map` хранит статическую информацию.
- [/cell.py](/cell.py) - класс `Cell`, реализующий клетку карты
- [/robot.py](/robot.py) - робот `Robot`, выполняющий действия.

#### До запуска
1. Для каждого робота модель резервирует клетку, соответствующую начальному положению.
2. Для каждого робота модель вызывает `Brain.add_robot`.
3. Для каждого робота модель узнает первое действие: вызывает `Brain.get_next_action`.

#### Во время исполнения
После того, как модель получило очередное действие очередного робота, она выполняет это действие следующим образом:
- **бездействовать**: модель добавляет событие, что робот закончит действие через заданное время
- **двигаться**: модель резервирует следующую клетку, добавляет событие через нужное для перемещения время, отменяет резервирование предыдущей клетки.
- **заряжаться**: робот заряжается
- **взять**: робот забирает посылку
- **положить**: робот кладёт посылку

После обработки очередного действия очередного робота, модель узнает для этого робота новое действие, вызывая `Brain.get_next_action`.

### Модель системы управления

#### Интерфейс
Модель системы управления необходимо реализовать на python специальным классом, который наследуется от класса `Brain` и состоит из методов:
- `add_robot(Robot)`, вызывается моделью склада для каждого добавленного робота до запуска модели.
- `get_next_action(Robot) -> Robot.Action`, вызывается моделью склада для каждого робота, метод возвращает предстоящее действие для данного робота.

#### Информация о состоянии модели склада
Модель система управления может получить всю информацию о текущем состоянии модели склада из поля `_model` (экземпляр класса `Model`), которое содержится в классе `Brain`.

Класс `Model`содержит неизменяемую часть - карта склада - поле `map` и переменною - состояние роботов - поле `robots`.

Карта склада может быть получена из полей карты `Map`:
- `inputs` - список координат пунктов получения
- `outputs` - список координат пунктов назначение
- `chargers` - список координат зарядных устройств
- `inputs_ids` - список id пунктов получение
- `outputs_ids` - список id пунктов назначения
- `charge_ids` - список id зарядных устройств

Каждая клетка содержит неизменяемые поля:
- `free` - может ли робот находиться на ней
- `input_id` - id пункта получения или `None`, если нет
- `output_id` - id пункта назначения или `None`, если нет
- `charge_id` - id зарядного устройства или `None`, если нет
- `reserved` - какой-то робот зарезервировал клетку - использует, другие не могут в нее перемещаться.

Каждый робот, содержит неизменяемые поля, соответствующие конфигурации:
- `id` - id робота, заданный конфигурацией. Если не задан, то будет `None`
- `type` - тип робота, информация о свойствах робота.

Поскольку переменная часть модели состоит только из состояния роботов, то о текущем состоянии модели склада можно узнать из полей класса `Robot`:
- `position.x`, `position.y` - целые координаты клетки, на которой находится робот (начиная с 0)
- `direction` одно из 4 направлений 
- `battery_capacity` - максимальный объём батареи
- `current_charge` - текущий заряд робота
- `robot_is_standing_` (`bool`) - параметр, который показывает стоит робот или же находится в движении.
- `is_going_to_charger_` (`bool`) - параметр, который показывает едет ли робот на зарядное устройство
- `mail` - посылка, которую везет робот или `None`, если нет посылки:
    - `mail.id`(`int`) - уникальный номер посылки
    - `mail.destination`(`int`) - направление, в которое нужно доставить


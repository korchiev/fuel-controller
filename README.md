# fuel-controller

Учебный контроллер АЗС. Протокол в этом репозитории выдуман для уроков. Это не Tatsuno SS-LAN, и эти байты нельзя отправлять на настоящую колонку.

## Кадр

Шесть байт:

```
START  ADDRESS  COMMAND  DATA  CHECKSUM  END
0x02   pump     cmd      byte  sum       0x03
```

`CHECKSUM = (ADDRESS + COMMAND + DATA) & 0xFF`

Команды учебного протокола:

| Команда | Байт | DATA |
| --- | --- | --- |
| GET_STATUS | `0x10` | `0` |
| AUTHORIZE | `0x20` | литры, 0..255 |
| STOP | `0x30` | `0` |
| START_FUELING | `0x40` | `0` |
| RESET | `0x50` | `0` |

Ответ колонки — такой же кадр. `COMMAND` равен `ACK` (`0x06`) или `NAK` (`0x15`). `DATA` — текущее состояние: `IDLE=0`, `AUTHORIZED=1`, `FUELING=2`, `FINISHED=3`.

Чужой адрес колонка игнорирует и молчит. Битый кадр со своим адресом получает NAK.

Пример из урока, «разрешить колонку 2 на 50 литров»:

```
02 02 20 32 54 03
```

## Состояния

```
IDLE --AUTHORIZE--> AUTHORIZED --START_FUELING--> FUELING --STOP--> FINISHED --RESET--> IDLE
```

Событие `reach_preset()` тоже переводит `FUELING` в `FINISHED`. Это не команда контроллера.

Команда не из этой таблицы не меняет состояние и получает NAK.

## Запуск

```bash
PYTHONPATH=src python examples/virtual_station.py
PYTHONPATH=src python -m pytest
```

`SerialTransport` переносит байты через COM-порт и не разбирает кадр. Лаборатория на двух USB-RS485 описана в [`lab/README.md`](lab/README.md).

# Утилита Supervisor

`supervisor` — это легковесная утилита, предназначенная для запуска и мониторинга произвольных команд. Она функционирует как обёртка, перехватывая запуск процессов, отслеживая их завершение или зависание (через heartbeat-файл) и автоматически перезапуская при сбое. Предназначена для сервисов, скриптов и демонов без встроенного watchdog.

## Возможности

*   **Запуск процесса**: Запускает указанную команду с её аргументами.
*   **Мониторинг состояния**: Непрерывно отслеживает состояние контролируемого процесса.
*   **Проверка Heartbeat**: Проверяет активность процесса через конфигурируемый heartbeat-файл.
*   **Автоматический перезапуск**: Перезапускает процесс при:
    *   Завершении процесса (с ненулевым кодом выхода).
    *   Таймауте heartbeat.
*   **Грациозное завершение**: Пытается грациозно завершить контролируемый процесс с использованием `SIGTERM` перед принудительным `SIGKILL`.
*   **Политики перезапуска**: Поддерживает конфигурируемое максимальное количество попыток перезапуска и экспоненциальный backoff для предотвращения "циклов смерти".
*   **Логирование**: Предоставляет детальное логирование событий, включая счётчики перезапусков и задержки backoff.

## Использование

```bash
./supervisor [ОПЦИИ] <команда> [аргументы...]
```

### Опции

*   `--timeout <секунды>`: Устанавливает таймаут heartbeat в секундах. Если heartbeat-файл не обновляется в течение этого периода, процесс считается неотвечающим и перезапускается. По умолчанию: `20` секунд.
*   `--initial-check-delay <секунды>`: Устанавливает начальную задержку в секундах перед тем, как `supervisor` начнёт проверять heartbeat-файл. Полезно для команд, которым требуется время на инициализацию. По умолчанию: `0` секунд.
*   `--heartbeat-file <путь>`: Указывает путь и имя heartbeat-файла. Это позволяет запускать несколько экземпляров `supervisor` одновременно без конфликтов. По умолчанию: `heartbeat.txt`.
*   `--grace-period <секунды>`: Устанавливает время в секундах, которое `supervisor` ждёт для грациозного завершения процесса после отправки `SIGTERM` перед отправкой `SIGKILL`. По умолчанию: `5` секунд.
*   `--max-restarts <количество>`: Устанавливает максимальное количество последовательных перезапусков. Если этот лимит достигнут, `supervisor` завершит работу. Используйте `-1` для бесконечных перезапусков. По умолчанию: `-1`.
*   `--backoff-factor <множитель>`: Устанавливает множитель для экспоненциального backoff между перезапусками. Задержка рассчитывается как `множитель * (2 ** количество_перезапусков)`. По умолчанию: `1` секунда.

### Примеры

**Базовое использование:**
```bash
./supervisor python3 client.py
```

**С пользовательским таймаутом и начальной задержкой:**
```bash
./supervisor --timeout 30 --initial-check-delay 10 python3 my_long_running_script.py
```

**Мониторинг процесса с периодическими сбоями и ограниченными перезапусками:**
```bash
./supervisor --max-restarts 5 --backoff-factor 2 python3 test_client.py crash_periodic 60
```

**Параллельный запуск нескольких Supervisor:**
```bash
# В терминале 1
./supervisor --heartbeat-file /tmp/heartbeat_app1.txt python3 client_app1.py

# В терминале 2
./supervisor --heartbeat-file /tmp/heartbeat_app2.txt python3 client_app2.py
```

## Клиентские приложения

Для эффективного мониторинга процесса `supervisor` контролируемое приложение должно периодически обновлять heartbeat-файл.

### `client.py` (Пример клиента)

Простой Python-скрипт, который непрерывно записывает текущую метку времени в `heartbeat.txt` каждые 5 секунд.

```python
import time
import logging

logging.basicConfig(level=logging.INFO)

def main():
    while True:
        with open("heartbeat.txt", "w") as f:
            f.write(str(time.time()))
        logging.info("Heartbeat sent")
        time.sleep(5)

if __name__ == "__main__":
    main()
```

### `test_client.py` (Продвинутый тестовый клиент)

Продвинутый клиент, разработанный для имитации различных сценариев для всестороннего тестирования `supervisor`. Он поддерживает:
*   `normal`: Нормальная работа, отправка heartbeat и грациозное завершение.
*   `crash_periodic`: Имитация периодических сбоев.
*   `hang`: Прекращает отправку heartbeat для имитации неотзывчивости.
*   `sigterm_test`: Ожидает сигнал `SIGTERM` для демонстрации грациозного завершения.
*   `long_request`: Имитирует длительную операцию без отправки heartbeat в течение указанной продолжительности.

Использование: `python3 test_client.py <сценарий> [продолжительность]`

```python
import time
import logging
import sys
import os
import random
import signal

logging.basicConfig(level=logging.INFO)
HEARTBEAT_FILE = "heartbeat.txt" # Примечание: В реальном использовании это должно быть настроено supervisor через аргумент CLI или переменную окружения

def write_heartbeat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))
    logging.info("Heartbeat sent")

def signal_handler(signum, frame):
    logging.info(f"Test client: Received signal {signum}. Exiting gracefully.")
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30 # Default duration for some scenarios

    if scenario == "normal":
        logging.info(f"Test client: Normal operation (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat()
            time.sleep(random.uniform(3, 7)) # Random pauses
        logging.info("Test client: Exiting normally.")
        sys.exit(0)
    elif scenario == "crash_periodic":
        logging.info(f"Test client: Simulating periodic crashes (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat()
            time.sleep(random.uniform(3, 7))
            if random.random() < 0.2: # 20% chance to crash
                logging.error("Test client: Simulating a random crash!")
                sys.exit(1)
        logging.info("Test client: Exiting normally after periodic crashes.")
        sys.exit(0)
    elif scenario == "hang":
        logging.info(f"Test client: Simulating a hang (sending heartbeat for 10 seconds, then stopping heartbeat and looping)")
        for i in range(2): # Send heartbeat for 10 seconds (2 * 5s)
            write_heartbeat()
            time.sleep(5)
        logging.warning("Test client: Stopping heartbeat and entering infinite loop. Supervisor should detect timeout.")
        while True:
            time.sleep(1) # Simulate busy work without heartbeat
    elif scenario == "sigterm_test":
        logging.info("Test client: Waiting for SIGTERM (sending heartbeat)")
        while True:
            write_heartbeat()
            time.sleep(5)
    elif scenario == "long_request":
        logging.info(f"Test client: Simulating a long request (sending heartbeat, then pausing for {duration}s without heartbeat)")
        write_heartbeat()
        logging.info(f"Test client: Starting long operation, no heartbeat for {duration} seconds.")
        time.sleep(duration) # Simulate long operation without heartbeat
        write_heartbeat() # Heartbeat after long operation
        logging.info("Test client: Long operation finished, heartbeat sent. Exiting.")
        sys.exit(0)
    else:
        logging.error(f"Unknown scenario: {scenario}")
        sys.exit(1)

if __name__ == "__main__":
    # Clean up heartbeat file before starting
    if os.path.exists(HEARTBEAT_FILE):
        os.remove(HEARTBEAT_FILE)
    main()
```
<line_count>167</line_count>
</write_to_file>
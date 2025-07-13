# Утилита Supervisor

`supervisor` — это мощная **система управления процессами** и **инструмент для DevOps**, предназначенная для **мониторинга приложений** и запуска произвольных команд. Она функционирует как обёртка, обеспечивая **надежное выполнение** и **бесперебойную работу** ваших сервисов. `supervisor` перехватывает запуск процессов, отслеживает их завершение или зависание (через heartbeat-файл) и выполняет **автоматический перезапуск** при сбое. Это идеальное решение для **управления демонами**, скриптами и сервисами без встроенного watchdog, обеспечивая **управление жизненным циклом приложений** и **автоматизацию операций**.

## Возможности

*   **Запуск процесса**: `supervisor` запускает указанную команду с её аргументами, обеспечивая **управление задачами** и **контроль процессов**.
*   **Мониторинг состояния**: Непрерывно отслеживает состояние контролируемого процесса, гарантируя **надежность сервера** и **оптимизацию производительности**.
*   **Проверка Heartbeat (Опционально)**: Проверяет активность процесса через конфигурируемый heartbeat-файл, что критически важно для **мониторинга приложений**. **Отключено по умолчанию.**
*   **Автоматический перезапуск**: `supervisor` выполняет **автоматический перезапуск** процесса при:
    *   Завершении процесса (с ненулевым кодом выхода).
    *   Таймауте heartbeat (если включено), что способствует **бесперебойной работе**.
*   **Грациозное завершение**: Пытается грациозно завершить контролируемый процесс с использованием `SIGTERM` перед принудительным `SIGKILL`, обеспечивая чистое **управление сервисами**.
*   **Политики перезапуска**: Поддерживает конфигурируемое максимальное количество попыток перезапуска и экспоненциальный backoff для предотвращения "циклов смерти", повышая **надежность сервера**.
*   **Логирование**: Предоставляет детальное логирование событий, включая счётчики перезапусков и задержки backoff, с чётким префиксом `[SUPERVISOR]` для различения его логов, что упрощает **управление фоновыми задачами** и **развертывание приложений**.

## Использование

```bash
./supervisor [ОПЦИИ] <команда> [аргументы...]
```

### Опции

*   `--timeout <секунды>`: Устанавливает таймаут heartbeat в секундах. Если heartbeat-файл не обновляется в течение этого периода, процесс считается неотвечающим и перезапускается. **Применимо только если heartbeat включен.** По умолчанию: `20` секунд.
*   `--initial-check-delay <секунды>`: Устанавливает начальную задержку в секундах перед тем, как `supervisor` начнёт проверять heartbeat-файл. Полезно для команд, которым требуется время на инициализацию. По умолчанию: `0` секунд.
*   `--heartbeat-file <путь>`: Указывает путь и имя heartbeat-файла. Это позволяет запускать несколько экземпляров `supervisor` одновременно без конфликтов. **Применимо только если heartbeat включен.** По умолчанию: `heartbeat.txt`.
*   `--grace-period <секунды>`: Устанавливает время в секундах, которое `supervisor` ждёт для грациозного завершения процесса после отправки `SIGTERM` перед отправкой `SIGKILL`. По умолчанию: `5` секунд.
*   `--max-restarts <количество>`: Устанавливает максимальное количество последовательных перезапусков. Если этот лимит достигнут, `supervisor` завершит работу. Используйте `-1` для бесконечных перезапусков. По умолчанию: `-1`.
*   `--backoff-factor <множитель>`: Устанавливает множитель для экспоненциального backoff между перезапусками. Задержка рассчитывается как `множитель * (2 ** количество_перезапусков)`. По умолчанию: `1` секунда.
*   `--enable-heartbeat`: Явно включает механизм heartbeat. **Heartbeat отключен по умолчанию.**

### Примеры

**Базовое использование (Heartbeat отключен):**
```bash
./supervisor python3 client.py
```

**С включенным Heartbeat и пользовательским таймаутом:**
```bash
./supervisor --enable-heartbeat --timeout 30 python3 my_long_running_script.py
```

**Мониторинг процесса с периодическими сбоями, ограниченными перезапусками и включенным Heartbeat:**
```bash
./supervisor --enable-heartbeat --max-restarts 5 --backoff-factor 2 python3 test_client.py crash_periodic 60
```

**Параллельный запуск нескольких Supervisor с включенным Heartbeat:**
```bash
# В терминале 1
./supervisor --enable-heartbeat --heartbeat-file /tmp/heartbeat_app1.txt python3 client_app1.py

# В терминале 2
./supervisor --enable-heartbeat --heartbeat-file /tmp/heartbeat_app2.txt python3 client_app2.py
```

## Клиентские приложения

Для эффективного мониторинга процесса `supervisor` с использованием механизма heartbeat, контролируемое приложение должно периодически обновлять heartbeat-файл. Путь к этому файлу должен быть передан клиентскому приложению `supervisor` (например, через аргументы командной строки или переменные окружения).

### `client.py` (Пример клиента)

Простой Python-скрипт, который непрерывно записывает текущую метку времени в указанный heartbeat-файл (или `heartbeat.txt` по умолчанию) каждые 5 секунд.

```python
import time
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)

HEARTBEAT_FILE = "heartbeat.txt" # Default value

def main():
    global HEARTBEAT_FILE
    if len(sys.argv) > 1:
        HEARTBEAT_FILE = sys.argv[1]
        logging.info(f"Using heartbeat file: {HEARTBEAT_FILE}")
    else:
        logging.info(f"Using default heartbeat file: {HEARTBEAT_FILE}")

    while True:
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                f.write(str(time.time()))
            logging.info("Heartbeat sent")
        except IOError as e:
            logging.error(f"Error writing to heartbeat file {HEARTBEAT_FILE}: {e}")
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

Использование: `python3 test_client.py <сценарий> [продолжительность] [путь_к_heartbeat_файлу]`

```python
import time
import logging
import sys
import os
import random
import signal

logging.basicConfig(level=logging.INFO)

HEARTBEAT_FILE = "heartbeat.txt" # Default value

def write_heartbeat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))
    logging.info("Heartbeat sent")

def signal_handler(signum, frame):
    logging.info(f"Test client: Received signal {signum}. Exiting gracefully.")
    # No need to remove heartbeat file here, atexit in supervisor handles it
    sys.exit(0)

def main():
    global HEARTBEAT_FILE
    
    # Parse heartbeat file argument if provided
    # The heartbeat file argument for test_client.py will be the second argument after the scenario
    # e.g., python3 test_client.py normal heartbeat_test.txt
    # or python3 test_client.py normal 30 heartbeat_test.txt
    
    # Find the last argument that is not a number (scenario or duration)
    # This is a simplified parsing for test_client, supervisor handles its own args
    
    # Check if the last argument is a file path
    if len(sys.argv) > 1 and not sys.argv[-1].isdigit():
        HEARTBEAT_FILE = sys.argv[-1]
        logging.info(f"Test client: Using custom heartbeat file: {HEARTBEAT_FILE}")
        # Remove heartbeat file from sys.argv for scenario parsing
        sys.argv.pop(-1)
    else:
        logging.info(f"Test client: Using default heartbeat file: {HEARTBEAT_FILE}")

    # Clean up heartbeat file before starting, only if it's the default one or explicitly managed by client
    # In a real scenario, supervisor would manage the heartbeat file.
    # For testing, we ensure a clean state for the client's perspective.
    if os.path.exists(HEARTBEAT_FILE):
        try:
            os.remove(HEARTBEAT_FILE)
            logging.info(f"Test client: Cleaned up old heartbeat file: {HEARTBEAT_FILE}")
        except OSError as e:
            logging.error(f"Test client: Error removing old heartbeat file {HEARTBEAT_FILE}: {e}")

    signal.signal(signal.SIGTERM, signal_handler)
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30 # Default duration for some scenarios

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
    main()
```
<line_count>168</line_count>
</write_to_file>
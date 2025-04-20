## Сборка базы данных с нуля

(1) Скачайте репозиторий:

```shell
git clone --depth=1 https://github.com/sasanarakkha/dpd-db-sbs.git
```

(2) Перейдите в директорию проекта:

```shell
cd dpd-db-sbs
```

(3) Загрузите подмодули из GitHub:

```shell
git submodule init && git submodule update
```

(4) Установите [Node.js](https://nodejs.org/en/download){target="_blank"} для вашей операционной системы.

(5) Установите [Go](https://go.dev/doc/install){target="_blank"} для вашей операционной системы.

(6) Установите [uv](https://astral.sh/uv/install){target="_blank"} для вашей операционной системы:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

(7) Установите все зависимости с помощью `uv`:

```shell
uv sync
```

(8) Наличие как минимум 20 ГБ оперативной памяти будет полезно. Если у вас меньше, рассмотрите возможность [увеличения объёма swap-памяти.](https://www.reddit.com/r/linuxmint/comments/uhjyir/how_to_increase_swap_size/?rdt=34113){target="_blank"}

(9) Один раз выполните инициализацию проекта:

```shell
uv run bash scripts/bash/initial_setup_run_once.sh
```

(10) Постройте базу данных — это может занять до часа при первом запуске:

```shell
uv run bash scripts/bash/initial_build_db.sh
```

В результате будет создан файл базы данных SQLite `dpd.db` в корневой папке проекта. Его можно открыть с помощью [DB Browser](https://sqlitebrowser.org/){target="_blank"}, [DBeaver](https://dbeaver.io/){target="_blank"}, через [SQLAlchemy](https://www.sqlalchemy.org/){target="_blank"} или другим удобным способом.

Краткое руководство по работе с этой базой данных через SQLAlchemy см. в разделе [использование базы данных](use_db.md)

---

## Дополнительная настройка

В проекте есть дополнительные модули, которые могут потребовать установки в зависимости от того, чем вы планируете пользоваться:

1. __Экспорт в GoldenDict__ требует установленной утилиты [dictzip](https://linux-packages.com/ubuntu-24-04/package/dictzip){target="_blank"}

2. Для запуска __графического интерфейса__ требуется установленный [tkinter](https://www.pythonguis.com/installation/install-tkinter-linux/){target="_blank"}

3. Для запуска __тестов базы данных__ могут понадобиться зависимости для [pyperclip](https://pyperclip.readthedocs.io/en/latest/index.html#not-implemented-error){target="_blank"}

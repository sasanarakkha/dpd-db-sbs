# Установка GoldenDict на Mac

## Кратко

1. Скачайте последнюю версию DPD [здесь](https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/).
2. Установите версию GoldenDict NG для [Apple Silicon M1 и выше](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/GoldenDict-24.05.05-Qt6.7.0-arm64.dmg) или [Intel AMD64](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/GoldenDict-24.05.05-Qt6.7.0-x86_64.dmg).
3. В настройках направьте GoldenDict в папку DPD.

Ниже подробные инструкции *anupubba*.

## Скачать GoldenDict

Если вы используете an Apple Silicon M1 или более позднюю версию, [скачайте эту версию GoldenDict NG с GitHub](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/GoldenDict-24.05.05-Qt6.7.0-arm64.dmg).

Если вы используете Intel AMD64, [скачайте эту версию GoldenDict NG с Github](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/GoldenDict-24.05.05-Qt6.7.0-x86_64.dmg).

<!-- Более подробную информацию о последней версии GoldenDict для Mac можно найти [здесь](https://github.com/goldendict/goldendict/wiki/Early-Access-Builds-for-Mac-OS-X).-->

## Установка GoldenDict

Дважды щелкните файл `GoldenDict.dmg` в папке Загрузки.

<!-- [download gd](../pics/mac-install/download%20gd.png)-->

Дважды щелкните установщик.

![goldendict install](../pics/mac-install/goldendict%20install.png)

Вероятно, вы получите предупреждение безопасности. Нажмите "Открыть в любом случае".

![warning](../pics/mac-install/warning.png)

Нажмите "Отмена" и откройте "Настройки безопасности и конфиденциальности". Нажмите на замочек в левом нижнем углу. Затем выберите "Открыть в любом случае", и GoldenDict откроется. Нажмите "Открыть в любом случае".

![allow gd](../pics/mac-install/allow%20gd.png)

Нажмите "Открыть" на следующем предупреждении безопасности.

![next security warning](../pics/mac-install/next%20security%20warning.png)

Установка завершена.

---

## Скачать DPD

Скачайте последнюю версию Цифрового Словаря Пали для GoldenDict с [Github](https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/) в вашу папку Загрузки.

## Распаковка

Найдите файл .zip в папке Загрузки и распакуйте его.

![unzip dpd](../pics/mac-install/unzip%20dpd.png)

## Создание папки GoldenDict

Рекомендуется создать легко доступную папку GoldenDict, например `/Documents/GoldenDict`.

![documents folder](../pics/mac-install/documents%20folder.png)

Скопируйте распакованную папку DPD в `/Documents/GoldenDict`.

![documents gd dpd](../pics/mac-install/documents%20gd%20dpd.png)

---

## Добавление словарей в GoldenDict

Запустите приложение GoldenDict.

Перейдите в Меню > Правка > Словари (Горячая клавиша **F3**).

![edit dictionaries](../pics/mac-install/edit%20dictionaries.png)

Перейдите в Источники > Файлы. Нажмите Добавить.

![sources files](../pics/mac-install/sources%20files.png)

Выберите папку `/Documents/GoldenDict`.

![select gd folder](../pics/mac-install/select%20gd%20folder.png)

Установите флажок "Рекурсивно" √ (это гарантирует поиск во вложенных папках).

![recursive](../pics/mac-install/recursive.png)

Нажмите "Пересканировать сейчас" или OK и подождите несколько моментов, пока словари индексируются.

![indexing](../pics/mac-install/indexing.png)

Всё готово!

---

Можно почитать, как [настроить горячую клавишу](setup_hotkey.md), чтобы вы могли щелкнуть по любому измененному слову Пали в любом тексте и немедленно открыть его в словаре.
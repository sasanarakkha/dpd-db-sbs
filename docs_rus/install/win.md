# Установка GoldenDict на Windows

## Вкратце

1. Скачайте последнюю версию DPD [здесь](https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/).
2. Установите свежую версию [GoldenDict](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/6.7.0-GoldenDict-ng-Installer.exe).
3. В настройках укажите GoldenDict папку с DPD.

Вот [видео](https://www.youtube.com/watch?v=KZ4CecdVL0k), чтобы помочь вам с установкой на Windows от [канала Learn Pali на Youtube](https://www.youtube.com/channel/UC73nNRzMzvweRb52ArFG3Gg).

Ниже приведены подробные *anupubba* инструкции в текстовом формате.

## Установка GoldenDict

Скачайте последнюю версию GoldenDict NG с [Github](https://github.com/xiaoyifang/goldendict-ng/releases/download/v24.05.05-LiXia.ecd1138c/6.7.0-GoldenDict-ng-Installer.exe).

Перейдите в вашу папку `Загрузки` и дважды щелкните `6.7.0-GoldenDict-ng-Installer.exe`.

<!-- [gd exe](../pics/win-install/gd%20exe.png) -->

Выберите ваш язык. Нажмите **OK**.

![select language](../pics/win-install/select%20language.png)

Нажмите **Далее >**.

![setup welcome](../pics/win-install/setup%20welcome.png)

Нажмите **Принимаю**.

![gd license](../pics/win-install/gd%20license.png)

Выберите место установки и нажмите **Далее >**.

![choose default install location](../pics/win-install/choose%20default%20install%20location.png)

Нажмите Установить.

![choose start menu folder](../pics/win-install/choose%20start%20menu%20folder.png)

Установка…

![installing](../pics/win-install/installing.png)

Нажмите Готово.

![install finished](../pics/win-install/install%20finshed.png)

## Скачать DPD

Скачайте последнюю версию Цифрового Словаря Пали с [Github](https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/).

## Создание папки GoldenDict

Рекомендуется создать легко доступную папку GoldenDict, например `\Documents\GoldenDict`.

![goldendict folder](../pics/win-install/goldendict%20folder.png)

## Распаковка

Щелкните правой кнопкой мыши на файле .zip в папке Загрузки и выберите "Извлечь все".

![extract all](../pics/win-install/extract%20all.png)

Выберите папку `\Documents\GoldenDict` и нажмите Извлечь.

![extract to](../pics/win-install/extract%20to.png)

Теперь в `\Documents\GoldenDict` будет папка `DPD`.

![extracted folder](../pics/win-install/extracted%20folder.png)

## Настройка GoldenDict

Запустите GoldenDict из меню Пуск.

![gd icon](../pics/win-install/gd%20icon.png)

Откройте Меню > Правка > Словари (клавиша F3).

![edit dictionaries](../pics/win-install/edit%20dictionaries.png)

Нажмите Добавить.

![add button](../pics/win-install/add%20button.png)

Перейдите в `\Documents\GoldenDict` и нажмите Выбрать папку.

Установите флажок **Рекурсивно** (это гарантирует добавление всех подпапок). И нажимите **Пересканировать**

![recursive](../pics/win-install/recursive.png)

Подождите, пока словарь будет проиндексирован.

![indexing](../pics/win-install/indexing.png)

Всё готово!

---

Можно почитать, как [настроить горячую клавишу](setup_hotkey.md), чтобы вы могли щелкнуть на любое слово на Пали в любом тексте и мгновенно открыть его в словаре.
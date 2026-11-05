# DPD для KOReader

Читайте Пали с DPD прямо в [KOReader](https://koreader.rocks){target="_blank"} — бесплатном приложении для чтения электронных книг, которое работает на Kindle, Kobo, PocketBook и многих других устройствах.

Нажмите и удерживайте любое слово на Пали во время чтения, и на странице появится словарная статья DPD. Все значения отображаются вместе, составные слова разбиты на части, а таблицы грамматики доступны одним касанием. Закройте всплывающее окно, и вы вернётесь на свою страницу, точно на то же место.

Плагин создан [Дост. Ниродхавихари](https://github.com/nirodhav){target="_blank"} и использует полную мобильную базу данных DPD, поэтому работает офлайн, прямо на устройстве. Его можно бесплатно скачать со [страницы релизов плагина](https://github.com/digitalpalidictionary/dpd-koreader/releases/latest){target="_blank"}.

![DPD для KOReader: составные слова объясняются в одном поиске, все значения в одном окне, склонения и спряжения](../pics/koreader/hero_light.png#only-light)
![DPD для KOReader: составные слова объясняются в одном поиске, все значения в одном окне, склонения и спряжения](../pics/koreader/hero_dark.png#only-dark)

## Что он показывает

- все значения слова в одном всплывающем окне, а не по одному
- составные слова, разбитые на части, у каждой краткое значение — коснитесь части, чтобы развернуть её, или перейдите к её собственной словарной статье
- таблицы склонения и спряжения, корни, семейства и частота
- поиск на Пали или английском с подсказками написания
- другие словари DPD, такие как CPD и DPPN

Здесь при чтении ищется длинное составное слово из сутты. Каждая часть составного слова перечислена со своим значением:

![составное слово, найденное при чтении, разбитое на части](../pics/koreader/main_light.png#only-light){width="360"}
![составное слово, найденное при чтении, разбитое на части](../pics/koreader/main_dark.png#only-dark){width="360"}

А здесь значения слова *dhammaṃ*, одно из которых развёрнуто на месте:

![значения слова dhammaṃ, одно развёрнуто](../pics/koreader/lookup_light.png#only-light){width="360"}
![значения слова dhammaṃ, одно развёрнуто](../pics/koreader/lookup_dark.png#only-dark){width="360"}

## Установка

Вам понадобится KOReader версии v2026.07 или новее (на Kindle для этого потребуется техническая настройка) и около 1,1 ГБ свободного места.

1. Скачайте zip-файл плагина со [страницы релизов](https://github.com/digitalpalidictionary/dpd-koreader/releases/latest){target="_blank"} и распакуйте его в `koreader/plugins/` на устройстве.
2. Скачайте `dpd-mobile-db.zip` с [последнего релиза DPD](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"} и скопируйте находящийся внутри `dpd-mobile.db` в `koreader/data/dpd/`.
3. Перезапустите KOReader. **Database status** в меню DPD должен показывать **Database ready**, а для более новой базы данных — **Newer release, should work**.

Полные инструкции есть в [README](https://github.com/digitalpalidictionary/dpd-koreader#install){target="_blank"} плагина, который также входит в загрузку.

## Как поддерживать DPD в актуальном состоянии

### Плагин

Откройте **Help → Check for updates** в меню DPD, выберите **Install** и перезапустите KOReader. Ваши настройки сохранятся. Необязательные автоматические проверки (**Help → Check for updates automatically**) выполняются примерно раз в неделю и только когда Wi-Fi уже включён. Они уведомляют вас об обновлениях, но не устанавливают их автоматически.

Версиям 0.3.0 и более ранним сначала нужно одно ручное обновление: закройте KOReader, замените `koreader/plugins/dpd.koplugin` папкой из [нового zip-файла](https://github.com/digitalpalidictionary/dpd-koreader/releases/latest){target="_blank"} и перезапустите.

### База данных

Новый релиз DPD выходит каждый месяц, в день Упосатхи. Чтобы обновить:

1. Скачайте `dpd-mobile-db.zip` с [последнего релиза DPD](https://github.com/digitalpalidictionary/dpd-db/releases/latest){target="_blank"}.
2. Закройте KOReader, замените `koreader/data/dpd/dpd-mobile.db` новым файлом и удалите рядом с ним все файлы `-wal` и `-shm`.
3. Перезапустите KOReader. **Database status** в меню DPD покажет новый релиз.

Меню DPD находится в разделе **Search → Digital Pāḷi Dictionary**:

![меню DPD, показывающее Database: ready](../pics/koreader/database_status_menu_light.png#only-light){width="400"}
![меню DPD, показывающее Database: ready](../pics/koreader/database_status_menu_dark.png#only-dark){width="400"}

![Database status: Database ready](../pics/koreader/database_status_light.png#only-light){width="400"}
![Database status: Database ready](../pics/koreader/database_status_dark.png#only-dark){width="400"}

## Ошибки и обратная связь

Пожалуйста, сообщайте об ошибках в [системе отслеживания задач](https://github.com/digitalpalidictionary/dpd-koreader/issues){target="_blank"} или пишите на [dpd-koreader@nirodha.8shield.net](mailto:dpd-koreader@nirodha.8shield.net).

**КАК ПОДГОТОВИТЬ UBUNTU 24.04 К РАБОТЕ В РЕЖИМЕ КИОСКА С ОДНИМ ПРИЛОЖЕНИЕМ?**

**1. Выбор виртуальной машины.**

Данный способ был проверен на VMWare Workstation 17 Player и Oracle VM VirtualBox. Корректной работы удалось достичь только на Oracle VM VirtualBox 7.0, используя Ubuntu Desktop 24.04 LTS.

**2. Запуск и настройка операционной системы.**

Скачайте Ubuntu Desktop с официального сайта [Ubuntu](https://ubuntu.com/download/desktop) (предпочтительно скачивать Long-term support версии LTS). Затем завершите инициализацию системы, и создайте root пользователя и войдите под ним в систему.

![image](https://github.com/user-attachments/assets/be20cb7c-2d2b-4e1f-9869-bb9307fd3c3c)


Теперь создайте еще одного, на этот раз обычного, пользователя и добавьте его в файл sudoers. Вы можете это сделать командой _sudo adduser username sudo_ или дополнить файл **/etc/sudoers**, дописав в его конец _username ALL=(ALL) ALL_, теперь войдите в систему под только что созданным пользователем.

**3. Настройка приложения приложения.**

Скачайте и сохраните ваше приложение в любом удобном для вас директории. Откройте терминал (Ctrl + Alt + T) и измените права приложения командой _sudo chmod +x /path/to/you/app_ (Важно! Если ваше приложение ссылается на любые другие файлы, то необходимо для каждого файла также изменить права).

Теперь попробуйте запустить приложение. Для этого перейдите в директорию где располагается ваше приложение из терминала командой _cd /path/to/you/dir_, и запустите приложение _./YouApplication_. Если все работает корректно, то можете переходить к следующему пункуту.

**4. Создание исполняемого скрипта.**

Опционально. Если вы хотите чтобы ваше приложение вновь открывалось после того как пользователь случайно/намеренно вышел из него, то вам необходимо создать bash-скрипт. С помощью утилиты nano/vi/gedit создайте скрипт **you_script.sh**. 

Набираем текст скрипта:

![image](https://github.com/user-attachments/assets/9113985c-b57c-4e63-9d55-59e98b6262bc)



Сохраните скрипт и измените ему права также, как в вы уже делали в пункте 3. Проверьте исправность работы скрипта командой _sh /path/to/you/script.sh_. 

**5. Отключение X.**

Чтобы пользователь не смог нажать ничего лишнего, необходимо привести систему в режим киоска. Такой режим подразумевает ограниченные возможности пользователя, упрощенный интерфейс, блокировка большинства комбинаций клавиш.

Начнем с перехода системы в console mode. Для этого в терминале напишите _sudo systemctl set-default multi-user.target_, теперь при входе в систему вы автоматически будете находиться в системе с отключенными X (console mode). Перезайдите в систему, быстро сделать это можно командой _sudo reboot_. Если вы хотите включить вход с графическим интерфейсом по умолчанию напишите _sudo systemctl set-default graphical.target_.

(Однако вы также можете переключаться между сессиями tty* по нажатию Ctrl + Alt + F*, чтобы переходить в console mode. По умолчанию F3. А чтобы вернуться в графический интерфейс F2.)

**6. Запуск приложения в режиме киоска.**

Войдите в систему под созданным ранее обычным пользователем. Если вы не создавали скрипт из пункта 4, то перейдите в директорию с приложением как было показано ранее и запустите приложение командой _startx ./YouApplication_. Если вы создавали скрипт, то напишите _startx /path/to/you/scrip.sh_.

Пример того, как может выглядеть приложение в режиме киоска:

![image](https://github.com/user-attachments/assets/fd0890a6-d8f5-4951-9bd5-52fe633239a5)


Проверьте корректность работы вашего приложения.

Поздравляю! Вы справлись!🥳


### django-messenger

![image](https://user-images.githubusercontent.com/53310434/210276929-f85d0671-714d-4599-9893-25f62499648d.png)

```
Проект-мессенджер, где можно общаться в чат комнатах по несколько человек
или же в личных сообщениях.
```

### Разработчики:

```
https://github.com/Drvmnekta
Бэкенд
```

```
https://github.com/Kseniya8
Фронтэнд
```

- Разработан функционал пагинации в обе стороны - подгрузка пулла новых или старых сообщений.
- Есть возможность видеть прочитано ли ваше сообщение.
- Для пользователя выводится кол-во непрочитанных сообщений.
- Изначально чатбокс фокусируется на самом новом сообщении, и если их больше 20 - появляется кнопка для прокрутки сообщений до самого последнего с указанием количества непрочитанных.
- Реализована возможность видеть онлайн-собеседников, а также когда они присоединились или покинули чат.

# Использованные технологии
- WebSocket: DjangoChannels
- DB: SQLite
- Back: Django, python
- Front: HTML5, нативный JS, CSS, bootstrap

import telebot
from telebot import types
import threading
from datetime import datetime as dt

TOKEN = "6574073483:AAEvhURhiy8DZDmZVuz_gEl7x3wxFznRNAg"
bot = telebot.TeleBot(TOKEN)


class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.tasks = []
        self.reminders = []

    def del_task(self, index):
        del self.tasks[index]

    def del_reminders(self, text):
        for index, value in enumerate(self.reminders):
            if value[1] == text:
                del self.reminders[index]
                return

    def stop(self, text):
        for index, value in enumerate(self.reminders):
            if value[1] == text:
                value[2].cancel()


users = {}


def create_keyboard(text):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text, callback_data='cancel_task')
    markup.add(button)
    return markup


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_task')
def cancel_task(call):
    user_id = call.from_user.id
    bot.clear_step_handler_by_chat_id(user_id)
    bot.send_message(user_id, 'Задача отменена', reply_markup=types.ReplyKeyboardRemove())
    bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                  reply_markup=None)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = User(user_id)
    start_message = (
        "Привет! Я бот-планировщик задач.\n"
        "Я помогу вам организовать свои задачи:\n\n"
        "➕ /add - добавить новую задачу\n"
        "📋 /list - посмотреть список задач\n"
        "✅ /done - отметить выполненную задачу\n"
        "➕ /remind - добавить напоминание\n"
        "➖ /remind_remove - удалить напоминание\n"
        "📋 /remind_list - посмотреть список напоминаний \n\n"
        "Просто отправьте мне команду, чтобы начать!"
    )
    bot.send_message(user_id, start_message)


@bot.message_handler(commands=['add'])
def add_task(message):
    user_id = message.from_user.id
    markup = create_keyboard("Отменить добавление задачи")
    sent_message = bot.send_message(user_id, "Введите описание задачи:", reply_markup=markup)
    bot.register_next_step_handler(message, process_new_task, user_id=user_id, sent_message=sent_message)


def process_new_task(message, user_id, sent_message):
    task_description = message.text
    users[user_id].tasks.append(task_description)
    bot.edit_message_reply_markup(chat_id=user_id, message_id=sent_message.message_id, reply_markup=None)
    bot.send_message(user_id, "Задача добавлена!")


@bot.message_handler(commands=['list'])
def list_tasks(message):
    user_id = message.from_user.id
    tasks = users[user_id].tasks
    if not tasks:
        bot.send_message(user_id, "Список задач пуст.")
    else:
        task_list = "\n".join(f"{index + 1}. {task}" for index, task in enumerate(tasks))
        bot.send_message(user_id, "Список задач:\n" + task_list)


@bot.message_handler(commands=['done'])
def mark_done(message):
    user_id = message.from_user.id
    tasks = users[user_id].tasks
    if not tasks:
        bot.send_message(user_id, "Список задач пуст.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    task_buttons = [types.KeyboardButton(f"{index + 1}. " + task) for index, task in enumerate(tasks)]
    back_button = types.KeyboardButton("ОТМЕНА")
    markup.add(back_button, *task_buttons)

    bot.send_message(user_id, "Выберите задачу для отметки выполнения:",
                     reply_markup=markup)
    bot.register_next_step_handler(message,
                                   process_done_task, user_id=user_id, tasks=tasks)


def process_done_task(message, user_id, tasks):
    task_done = message.text
    if task_done == 'ОТМЕНА':
        bot.send_message(user_id, "Отмена.",
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        try:
            len_tasks = len(str(len(tasks)))
            number = int(task_done[0: len_tasks]) - 1
            task_done = task_done[len_tasks + 2:]
            flag_1 = tasks[number] == task_done
            flag_2 = task_done[-1] == "…" and task_done[0:len(task_done) - 1] in tasks[number]

            if flag_1 or flag_2:
                users[user_id].del_task(number)
                bot.send_message(user_id, f"Задача '{task_done}' отмечена как выполненная.",
                                 reply_markup=types.ReplyKeyboardRemove())
            else:
                bot.send_message(user_id,
                                 "Выберите задачу из списка.")
                bot.register_next_step_handler(message,
                                               process_done_task, user_id=user_id, tasks=tasks)

        except (IndexError, ValueError, TypeError) as e:
            bot.send_message(user_id,
                             "Выберите задачу из списка.")
            bot.register_next_step_handler(message,
                                           process_done_task, user_id=user_id, tasks=tasks)



@bot.message_handler(commands=['remind'])
def remind_task(message):
    user_id = message.from_user.id
    markup = create_keyboard("Отмена добавления заметки")

    sent_message = bot.send_message(user_id,
                                    "Введите дату и время напоминания\n в формате ДД.ММ.ГГ ЧЧ:ММ", reply_markup=markup)
    bot.register_next_step_handler(message,
                                   process_remind_datetime, user_id=user_id, sent_message=sent_message, markup=markup)


def process_remind_datetime(message, user_id, sent_message, markup):
    datetime_str = message.text
    try:
        remind_datetime = dt.strptime(datetime_str,
                                      '%d.%m.%y %H:%M')
        bot.edit_message_reply_markup(chat_id=user_id, message_id=sent_message.message_id,
                                      reply_markup=None)
        sent_message = bot.send_message(user_id,
                                        "Введите текст напоминания:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: process_remind_text(msg, sent_message,
                                                                                remind_datetime))
    except ValueError:

        bot.edit_message_reply_markup(chat_id=user_id, message_id=sent_message.message_id, reply_markup=None)

        sent_message = bot.send_message(user_id,
                                        "Неверный формат даты и времени. Пожалуйста, используйте ДД.ММ.ГГ ЧЧ:ММ.",
                                        reply_markup=markup)

        bot.register_next_step_handler(message,
                                       process_remind_datetime, user_id=user_id, sent_message=sent_message,
                                       markup=markup)


def process_remind_text(message, sent_message, remind_datetime):
    user_id = message.from_user.id
    bot.edit_message_reply_markup(chat_id=user_id, message_id=sent_message.message_id,
                                  reply_markup=None)
    remind_text = message.text

    current_datetime = dt.now()
    time_difference = (remind_datetime - current_datetime).total_seconds()

    if time_difference > 0:
        timer = threading.Timer(time_difference, send_reminder, args=(user_id, remind_text))
        timer.start()
        users[user_id].reminders.append((remind_datetime, remind_text, timer))
        bot.send_message(user_id,
                         f"Напоминание установлено на {remind_datetime.strftime('%d.%m.%y %H:%M')}.")
    else:
        bot.send_message(user_id,
                         "Указанное время уже прошло. Невозможно установить напоминание.")


def send_reminder(user_id, remind_text):
    bot.send_message(user_id, f"Напоминание: {remind_text}")
    users[user_id].del_reminders(remind_text)


@bot.message_handler(commands=['remind_list'])
def remind_list(message):
    user_id = message.from_user.id
    reminders = users[user_id].reminders
    if not reminders:
        bot.send_message(user_id, "Список напоминаний пуст.")
    else:
        remind_list = "\n".join(
            f"{index + 1}. {remind[0].strftime('%d.%m.%y %H:%M')} - {remind[1]}" for index, remind in
            enumerate(reminders))
        bot.send_message(user_id,
                         "Список напоминаний:\n" + remind_list)


@bot.message_handler(commands=['remind_remove'])
def remind_remove(message):
    user_id = message.from_user.id
    reminders = users[user_id].reminders
    if not reminders:
        bot.send_message(user_id, "Список напоминаний пуст.")
    else:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        reminder_buttons = [types.KeyboardButton(f"{index + 1}. {remind[0].strftime('%d.%m.%y %H:%M')} - {remind[1]}") for index, remind in enumerate(reminders)]
        back_button = types.KeyboardButton("Назад")
        markup.add(*reminder_buttons, back_button)
        bot.send_message(user_id, "Выберите напоминание для удаления:",
                         reply_markup=markup)
        bot.register_next_step_handler(message,
                                       process_remind_remove, user_id=user_id, reminders=reminders)


def process_remind_remove(message, user_id, reminders):
    reminder = message.text
    if reminder == "Назад":
        bot.send_message(user_id, "Возвращаюсь в главное меню...",
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        try:
            len_reminds = len(str(len(reminders)))
            number = int(reminder[0: len_reminds]) - 1
            remind_datetime = reminder[len_reminds + 2: len_reminds + 16]
            remind_text = reminder[len_reminds + 19:]
            flag_1 = remind_text == reminders[number][1]
            flag_2 = remind_text[-1] == "…" and remind_text[0: len(remind_text) - 1] in reminders[number][1]
            flag = flag_2 or flag_1
            flag_3 = remind_datetime == reminders[number][0].strftime('%d.%m.%y %H:%M')
            if flag and flag_3:
                users[user_id].stop(reminders[number][1])
                users[user_id].del_reminders(reminders[number][1])
                bot.send_message(user_id, f"Напоминание '{remind_text}' удалено.", reply_markup=types.ReplyKeyboardRemove())
            else:
                bot.send_message(user_id, "Выберите напоминание из списка или нажмите 'Назад'.")
                bot.register_next_step_handler(message,
                                               process_remind_remove, user_id=user_id, reminders=reminders)
        except (IndexError, ValueError, TypeError):
            bot.send_message(user_id, "Выберите напоминание из списка или нажмите 'Назад'.")
            bot.register_next_step_handler(message,
                                           process_remind_remove, user_id=user_id, reminders=reminders)



if __name__ == '__main__':
    bot.polling(none_stop=True)
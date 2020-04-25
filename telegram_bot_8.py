from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from functools import reduce
import random
import json
import copy

TESTFILE = "tests.json"
tests = {}

WAIT_ANSWER = 1

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(update, context):
    update.message.reply_text("Пройдите тест. Ответьте на следующие вопросы.")

    # Перемешиваем порядок тестов и запоминаем его для данного пользователя.
    global tests
    context.user_data["tests"] = copy.deepcopy(tests)
    random.shuffle(context.user_data["tests"])

    # Задаем первый вопрос.
    context.user_data["test_id"] = 0
    update.message.reply_text(context.user_data["tests"][0]["question"])

    return WAIT_ANSWER


def stop(update, context):
    update.message.reply_text("Прерываем тест. До новых встреч!")
    context.user_data.clear()
    return ConversationHandler.END


def count_correct_results(tests):
    # считаем количество правильных ответов.
    return reduce(lambda s, t: s + int(t["correct_answer"]), tests, 0)


def wait_answer(update, context):
    # Принимаем и проверяем ответ. Записываем флаг корректного ответа в тест.
    response = update.message.text
    test_id = context.user_data["test_id"]
    context.user_data["tests"][test_id]["correct_answer"] = (response == context.user_data["tests"][test_id]["response"])

    # Ищем следующий тест. Если еще остались незаданные вопросы -- задаем.
    test_id += 1
    if test_id < len(context.user_data["tests"]):
        context.user_data["test_id"] = test_id
        update.message.reply_text(context.user_data["tests"][test_id]["question"])
        return WAIT_ANSWER
    # ... в противном случае подводим итоги и сбрасываем данные пользователя.
    else:
        update.message.reply_text(
            "Правильно: {0} из {1}.".format(count_correct_results(context.user_data["tests"]), len(context.user_data["tests"])))
        context.user_data.clear()
        return ConversationHandler.END


def main():
    # Загружаем тесты.
    global tests
    with open(TESTFILE, encoding="utf8") as f:
        tests = json.load(f)["test"]

    updater = Updater("YOUR_TOKEN", use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            WAIT_ANSWER: [
                MessageHandler(Filters.text, wait_answer, pass_user_data=True)
            ]
        },

        fallbacks=[CommandHandler('stop', stop, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

import logging
import telegram
import datetime
import calendar
import locale
from datetime import datetime as dt
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler,
                          CallbackContext, Handler)
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)
import tacticenv
from pyasm.security import Batch
from pyasm.search import Search
from pyasm.search.sql import Insert, Update, DbResource
from pprint import pprint
from src.pyasm.search import DbContainer

TOKEN = "TELEGRAM_TOKEN"

DEFAULT_PROJECT = 'dolly3d'
EPISODES = 'complex/scenes'

MY_ERROR_MESSAGE = 'Обратитесь к разработчику - sanycht@gmail.com'

DAYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
        '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
MONTH_NAME = list(calendar.month_abbr)[1:]
MONTH_NUMBER = [str(i) for i in range(1, 13)]
YEAR = [str(x) for x in range(dt.today().year, dt.today().year+2)]

MONTHS = {'01': ['january', 'jan', 'январь', 'января', 'янв'],
          '02': ['february', 'feb', 'февраль', 'февраля', 'фев'],
          '03': ['march', 'mar', 'марта', 'мар', 'март'],
          '04': ['april', 'apr', 'апрель', 'апреля', 'апр'],
          '05': ['may', 'май', 'мая'],
          '06': ['june', 'июнь', 'июня'],
          '07': ['july', 'июль', 'июля'],
          '08': ['august', 'aug', 'август', 'августа', 'авг'],
          '09': ['september', 'sep', 'сентябрь', 'сентября', 'сен'],
          '10': ['october', 'oct', 'октябрь', 'октября', 'окт'],
          '11': ['november', 'nov', 'ноября', 'ноябрь', 'нояб'],
          '12': ['december', 'dec', 'декабрь', 'декабря', 'дек']}

BTN_ADD = ['Добавить', 'add']
BTN_VIEW = ['Просмотр', 'view']
BTN_CANCEL = ['🚫Отмена', 'cancel']
BTN_BACK = ['⬅Назад', 'back']
BTN_YES = ['✅Да', 'yes']
BTN_NO = ['❎Нет', 'no']
BTN_DESCRIPTION = ['Описание', 'description']
BTN_ASSIGNED = ['Назачен', 'assigned']
BTN_STATUS = ['Статус', 'status']
BTN_BID_START = ['Начало', 'bid_start']
BTN_BID_END = ['Конец', 'bid_end']
BTN_CHECK = ['✔', 'check']
BTN_NEXT = ['▶', 'next']
BTN_PREV = ['◀', 'prev']
BTN_SAVE = ['💾', 'save']
BTN_TODAY = ['Сегодня', 'today']
LIMIT = 5

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

(MAIN_MENU, SEARCH_MENU, SELECTED_BUTTON, SELECTED_RECORD, SEARCH_EPISODES, SEARCH_ASSETS, SEARCH_USERS,
 SHOW_USERS, SHOW_EPISODE, TST_ASSETS, TASK_USER_NAVIGATION, TASK_EPISODE_NAVIGATION, TEST_EPISODE,
 EDIT_TASK_DESCRIPTION, SAVE_TASK_DESCRIPTION, ASK_SAVE_TASK_DESCRIPTION, ASK_SAVE_TASK_BID_START,
 SELECT_YEAR_FOR_TASK, SELECT_MONTH_FOR_TASK, SAVE_TASK_BID_START, ASK_SAVE_TASK_BID_START_2,
 ASK_SAVE_TASK_STATUS, SAVE_TASK_NEW_STATUS, SELECT_USER, ASK_SAVE_TASK_ASSIGNED, SAVE_TASK_ASSIGNED,
 TEST) = range(27)


#     def get_sobject_dict(sobject):
#         search_key = SearchKey.get_by_sobject(sobject, use_id=False)
#         sobj = sobject.get_data()
#         sobj['__search_key__'] = search_key
#         return sobj
#
#     def get_data():
#         Batch()
#         search = Search('sthpw/pipeline')
#         search.add_op('begin')
#         search.add_filter(name='name', value='Episodes')
#         stypes_pipelines = search.get_sobjects()
#         # process = Process
#         for pipeline in stypes_pipelines:
#             for process in pipeline.get_process_names():
#                 print(f'{pipeline.get_name()}: "{process}"')
#                 xml = pipeline.get_pipeline_xml()
#                 print(xml.get_value("label").to_string())

def get_data_for_s_menu(data):
    Batch()
    search = Search('sthpw/pipeline')
    search.add_op('begin')
    search.add_filter(name='code', value=data)
    pipelines = search.get_sobjects()
    btn_name = ['Показать всё', 'Поиск']
    call_data = ['show_all', 'search']
    for pipeline in pipelines:
        for process in pipeline.get_processes():
            if process.get_type() != 'progress':
                if process.get_task_pipeline() != 'task':
                    if process.get_label():
                        btn_name.append(process.get_label())
                    else:
                        btn_name.append(process.get_name())
                    call_data.append(process.get_name())
    btn_name.append(BTN_BACK[0])
    call_data.append(BTN_BACK[1])
    return [btn_name, call_data]


def get_group_list():
    Batch()
    search = Search('sthpw/login_group')
    groups = search.get_sobjects()
    btn_name = list()
    call_data = list()
    s = str()
    for group in groups:
        if group.get_code() not in ['admin', 'generalist']:
            s = group.get_code()
            btn_name.append(s.capitalize())
            call_data.append(group.get_code())
    btn_name.append(BTN_BACK[0])
    call_data.append(BTN_BACK[1])
    return [btn_name, call_data]


def get_users_in_group(group, task_cnt=True):
    def get_count(assigned):
        ss = Search.eval(f"@SOBJECT(sthpw/task['assigned', '{assigned}'])")
        return len(ss)

    Batch()
    result = Search.eval(f"@SOBJECT(sthpw/login_in_group['login_group', '{group}'].sthpw/login)")
    user_in_groups = list()
    user_name = list()
    if result:
        for res in result:
            user_in_groups.append(res.get_value('code'))
            if task_cnt:
                user_name.append(f"{res.get_value('display_name')} | {get_count(res.get_value('code'))}")
            else:
                user_name.append(f"{res.get_value('display_name')}")
    return [user_name, user_in_groups]


def search_menu(update: Update, context: CallbackContext):
    msg = 'Что будем искать'
    btn = None
    if update.callback_query.data == 'Episodes':
        btn = get_data_for_s_menu('dolly3d/scenes')
        kb = create_kbd(btn[0], btn[1], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SEARCH_EPISODES
    elif update.callback_query.data == 'Asset':
        btn = get_data_for_s_menu('dolly3d/assets')
        kb = create_kbd(btn[0], btn[1], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SEARCH_ASSETS
    elif update.callback_query.data == 'Users':
        btn = get_group_list()
        kb = create_kbd(btn[0], btn[1], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SEARCH_USERS


def get_pipeline_process(data):
    Batch()
    search = Search.eval(f"@SOBJECT(sthpw/pipeline['code', '{data}'])")
    for ss in search:
        process = ss.get_processes()
    return process


def get_task_count_for_episodes(process, status):
    Batch(DEFAULT_PROJECT)
    return len(Search.eval(f"@SOBJECT(sthpw/task['process','{process}']['status','{status}']."
                           f"complex/scenes.sthpw/task['process','{process}']['status','{status}'])"))


def test(update: Update, context: CallbackContext):
    pass


def episode_navigate(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_BACK[1]:
        # update.callback_query.data = 'Episodes'
        return search_episodes(update, context)
    else:
        context.bot_data['status'] = update.callback_query.data
        process = context.bot_data.get('process')
        status = update.callback_query.data
        tasks = get_task_for_episodes(process, status, limit=LIMIT, offset=0)
        context.bot_data['max_task'] = get_task_count_for_episodes(process, status)
        context.bot_data['next_step'] = 5
        context.bot_data['prev_step'] = 0
        msg = make_msg(tasks)
        btn_next_cap = f"5 - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        if context.bot_data.get('max_task') <= LIMIT:
            kb = create_kbd([BTN_BACK[0]], [BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_next_cap, BTN_BACK[0]], [BTN_NEXT[1], BTN_BACK[1]], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISODE_NAVIGATION


def show_all_episodes(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_BACK[1]:
        # update.callback_query.data = 'Episodes'
        return search_episodes(update, context)


def search_episodes(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_BACK[1]:
        return m_menu(update, context)
    elif update.callback_query.data == 'show_all':
        print('Show all')
    elif update.callback_query.data == 'search':
        print('Search')
    else:
        cd_process = update.callback_query.data
        context.bot_data['process'] = cd_process
        btn_name = ['Показать всё', 'Поиск']
        call_data = ['show_all', 'search']
        pipelines = get_pipeline_process('dolly3d/scenes')

        task_pipeline = ''
        for pipeline in pipelines:
            if update.callback_query.data == pipeline.get_name():
                task_pipeline = pipeline.get_task_pipeline()
        context.bot_data['current_task_pipeline'] = task_pipeline
        pipelines = get_pipeline_process(task_pipeline)
        for process in pipelines:
            btn_name.append(f"{process.get_name()} | {get_task_count_for_episodes(cd_process, process.get_name())}")
            call_data.append(process.get_name())
        context.bot_data['current_task_status'] = call_data[2:]
        msg = 'Выбери статус'
        btn_name.append(BTN_BACK[0])
        call_data.append(BTN_BACK[1])
        kb = create_kbd(btn_name, call_data, column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SHOW_EPISODE


def get_task_for_episodes(process, status, limit=5, offset=0):
    Batch(DEFAULT_PROJECT)
    tasks = []
    searches = Search('sthpw/task')
    searches.add_op('begin')
    searches.add_filter('process', f"{process}")
    searches.add_filter('status', f"{status}")

    searches2 = Search('complex/scenes')
    searches2.add_relationship_search_filter(searches)

    searches = Search('sthpw/task')
    searches.add_op('begin')
    searches.add_filter('process', f"{process}")
    searches.add_filter('status', f"{status}")
    searches.add_relationship_search_filter(searches2)
    searches.set_limit(limit)
    searches.set_offset(offset)
    search = searches.get_sobjects()
    tmp_ep = dict()
    for result in search:
        tmp_dict = result.get_sobject_dict()
        Batch(DEFAULT_PROJECT)
        s_obj = tmp_dict.get('search_type')
        exp = f"@SOBJECT({s_obj}['code', '{result.get('search_code')}'])"
        ep_desc = Search.eval(exp)
        if ep_desc:
            for ep in ep_desc:
                tmp_ep = ep.get_sobject_dict()
                if tmp_ep.get('name') != '':
                    tmp_dict['ep_name'] = tmp_ep.get('name')
                else:
                    tmp_dict['ep_name'] = ''

                if tmp_ep.get('description') != '':
                    tmp_dict['ep_description'] = ep.get_description()
                else:
                    tmp_dict['ep_description'] = 'None'
        else:
            tmp_dict['ep_description'] = ''
            tmp_dict['ep_name'] = ''
        tmp_dict['ep_ppl'] = tmp_ep.get('pipeline_code')
        tasks.append(tmp_dict)
    return tasks


def show_episode(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_BACK[1]:
        update.callback_query.data = 'Episodes'
        return search_menu(update, context)
    else:
        context.bot_data['status'] = update.callback_query.data
        process = context.bot_data.get('process')
        status = update.callback_query.data
        tasks = get_task_for_episodes(process, status, limit=LIMIT, offset=0)
        context.bot_data['max_task'] = get_task_count_for_episodes(process, status)
        context.bot_data['next_step'] = 5
        context.bot_data['prev_step'] = 0
        msg = make_msg(tasks)
        btn_next_cap = f"5 - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        if context.bot_data.get('max_task') <= LIMIT:
            kb = create_kbd([BTN_BACK[0]], [BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_next_cap, BTN_BACK[0]], [BTN_NEXT[1], BTN_BACK[1]], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISODE_NAVIGATION


def make_btn(tasks: []):
    data = []
    btn_name = []
    callback_data = []
    if tasks:
        for task in tasks:
            task_code = task['code']
            episode_code = task['search_code']
            if task_code:
                btn_name.append(f"Изменить {task_code}")
                callback_data.append(task_code)
    return btn_name, callback_data


def episode_task_navigate(update: Update, context: CallbackContext):
    process = context.bot_data.get('process')
    status = context.bot_data.get('status')
    if update.callback_query.data == BTN_BACK[1]:
        update.callback_query.data = context.bot_data.get('process')
        return search_episodes(update, context)
    elif update.callback_query.data == BTN_NEXT[1]:
        step = context.bot_data.get('next_step')
        tasks = get_task_for_episodes(process, status, limit=5, offset=step)
        context.bot_data['next_step'] = step + 5
        context.bot_data['prev_step'] = step - 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        btn_prev_cap = f"{BTN_PREV[0]} {context.bot_data.get('prev_step') + 5} - {context.bot_data.get('max_task')}"
        if context.bot_data['next_step'] >= context.bot_data['max_task']:
            kb = create_kbd([btn_prev_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_NEXT[1], BTN_BACK[1]], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISODE_NAVIGATION
    elif update.callback_query.data == BTN_PREV[1]:
        step = context.bot_data.get('prev_step')
        tasks = get_task_for_episodes(process, status, limit=5, offset=step)
        context.bot_data['prev_step'] = step - 5
        context.bot_data['next_step'] = step + 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        btn_prev_cap = f"{BTN_PREV[0]} {context.bot_data.get('prev_step') + 5} - {context.bot_data.get('max_task')}"
        if context.bot_data['prev_step'] < 0:
            context.bot_data['prev_step'] = 0
            kb = create_kbd([btn_next_cap, BTN_BACK[0]], [BTN_NEXT[1], BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_NEXT[1], BTN_BACK[1]], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISODE_NAVIGATION


def get_task(code):
    Batch(DEFAULT_PROJECT)
    searches = Search.eval(f"@SOBJECT(sthpw/task['code','{code}'])")
    for search in searches:
        task = search.get_sobject_dict()
    return task


def get_episode(code):
    Batch(DEFAULT_PROJECT)
    scene = dict()
    searches = Search.eval(f"@SOBJECT(complex/scenes['code','{code}'])")
    for search in searches:
        scene = search.get_sobject_dict()
    return scene


def get_scene_msg(scene):
    name = scene.get("name")
    name = f"#{name.replace(' ', '_').replace('.', '_')} "
    code = f"/{scene['code']}"
    description = f"{scene['description']}\n"
    msg = name + description + code
    return msg


def edit_episode(update: Update, context: CallbackContext):
    if update.message:
        tmp_str = update.message.text
        # Проверка сообщения на выбор пользователем задачи или эпизода
        if tmp_str.find('TASK') == -1:  # Пользователь выбрал Эпизод
            cmd = update.message.text[1:]
            msg = f"Изменение эпизода № {cmd}"
            context.bot_data['EPISODE_NUM'] = cmd
            context.bot_data['TASK_NUM'] = ''
            kb = create_kbd(['Имя эпизода', BTN_DESCRIPTION[0], BTN_BACK[0]],
                            ['ep_name', BTN_DESCRIPTION[1], BTN_BACK[1]],
                            row=False, column=2)
        else:   # Пользователь выбрал Задача
            cmd = update.message.text[1:]   # Помещаем в cmd номер задачи без /
            context.bot_data['TASK_NUM'] = cmd  # Сохраняем номер задачи для дальнейшего использования
            context.bot_data['EPISODE_NUM'] = ''    # Удаляем номер Эпизода
            context.bot_data['TASK_DESCRIPTION'] = get_task(cmd)    # Запоминаем данные Задачи из БД, что бы повторно
                                                                    # не делать запрос к БД
            task = context.bot_data.get('TASK_DESCRIPTION')
            context.bot_data['SCENE_DATA'] = get_episode(task.get('search_code'))
            # Фомируем сообщение
            msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                  f"\nИзменение задачи № {cmd}:\n" \
                  f"Назначен: {task.get('assigned')}\n" \
                  f"Описание: {task.get('description')}\n" \
                  f"Статус: {task.get('status')}\n" \
                  f"Начало: {task.get('bid_start_date')}\n" \
                  f"Конец: {task.get('bid_end_date')}"
            # Формируем кнопки
            kb = create_kbd([BTN_STATUS[0], BTN_DESCRIPTION[0], BTN_ASSIGNED[0], BTN_BID_START[0], BTN_BID_END[0], BTN_BACK[0]],
                            [BTN_STATUS[1], BTN_DESCRIPTION[1], BTN_ASSIGNED[1], BTN_BID_START[1], BTN_BID_END[1], BTN_BACK[1]],
                            row=False, column=2)
        # Удаляем последние два сообщения
        context.bot.deleteMessage(message_id=update.message.message_id-1, chat_id=update.message.chat_id)
        context.bot.deleteMessage(message_id=update.message.message_id, chat_id=update.message.chat_id)
        # Выводим сообщение
        update.message.reply_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return EDIT_TASK_DESCRIPTION    # Переходим на редактирование описания
    elif update.callback_query.data == BTN_BACK[1]:     # Нажата кнопка назад
        update.callback_query.data = BTN_NEXT[1]
        return TASK_EPISODE_NAVIGATION
    elif update.callback_query.message.text == context.bot_data.get('TASK_NUM'):
        tmp_str = update.callback_query.message.text
        if tmp_str.find('TASK') == -1:
            cmd = context.bot_data.get('TASK_NUM')
            msg = f"Изменение эпизода № {cmd}"
            context.bot_data['EPISODE_NUM'] = cmd
            context.bot_data['TASK_NUM'] = ''
            kb = create_kbd(['Имя эпизода', BTN_DESCRIPTION[0], BTN_BACK[0]],
                            ['ep_name', BTN_DESCRIPTION[1], BTN_BACK[1]],
                            row=False, column=2)
        else:
            cmd = context.bot_data.get('TASK_NUM')
            context.bot_data['TASK_NUM'] = cmd
            context.bot_data['EPISODE_NUM'] = ''
            task = context.bot_data.get('TASK_DESCRIPTION')
            msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                  f"\nИзменение задачи № {cmd}:\n" \
                  f"Назначен: {task.get('assigned')}\n" \
                  f"Описание: {task.get('description')}\n" \
                  f"Статус: {task.get('status')}\n" \
                  f"Начало: {task.get('bid_start_date')}\n" \
                  f"Конец: {task.get('bid_end_date')}"
            kb = create_kbd([BTN_STATUS[0], BTN_DESCRIPTION[0], BTN_ASSIGNED[0], BTN_BID_START[0], BTN_BID_END[0], BTN_BACK[0]],
                            [BTN_STATUS[1], BTN_DESCRIPTION[1], BTN_ASSIGNED[1], BTN_BID_START[1], BTN_BID_END[1], BTN_BACK[1]],
                            row=False, column=2)

        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return EDIT_TASK_DESCRIPTION


def selected_edit_task_button(update: Update, context: CallbackContext):
    cb = update.callback_query.data
    if cb == BTN_DESCRIPTION[1]:
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"<b>Описание:</b> <i>{task.get('description')}</i>\n" \
              f"Статус: {task.get('status')}\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n" \
              f"Введи новое описание"
        kb = create_kbd([BTN_BACK[0]], [BTN_BACK[1]])
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return ASK_SAVE_TASK_DESCRIPTION
    elif cb == BTN_BID_START[1]:
        context.bot_data['BID_START_OR_END'] = True
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"Описание: {task.get('description')}\n" \
              f"Статус: {task.get('status')}\n" \
              f"<b>Начало:</b> <i>{task.get('bid_start_date')}</i>\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Введи новую дату BID START с клавиатуры (например 12.05.2022 или 10 августа 22) или выбери год:"
        btn_name = YEAR + [BTN_TODAY[0], BTN_BACK[0]]
        btn_cb = YEAR + [BTN_TODAY[1], BTN_BACK[1]]
        kb = create_kbd(btn_name, btn_cb, column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SELECT_YEAR_FOR_TASK
    elif cb == BTN_BID_END[1]:
        context.bot_data['BID_START_OR_END'] = False
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"Описание: {task.get('description')}\n" \
              f"Статус: {task.get('status')}\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"<b>Конец:</b> <i>{task.get('bid_end_date')}</i>\n\n" \
              f"Введи новую дату BID END с клавиатуры (например 12.05.2022 или 10 августа 22) или выбери год:"
        btn_name = YEAR + [BTN_TODAY[0], BTN_BACK[0]]
        btn_cb = YEAR + [BTN_TODAY[1], BTN_BACK[1]]
        kb = create_kbd(btn_name, btn_cb, column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SELECT_YEAR_FOR_TASK
    elif cb == BTN_STATUS[1]:
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"Описание: {task.get('description')}\n" \
              f"<b>Статус:</b> <i>{task.get('status')}</i>\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Выбери статус"
        btn_name = context.bot_data.get('current_task_status') + [BTN_BACK[0]]
        btn_cb = context.bot_data.get('current_task_status') + [BTN_BACK[1]]
        kb = create_kbd(btn_name, btn_cb, column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return ASK_SAVE_TASK_STATUS
    elif cb == BTN_ASSIGNED[1]:
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"<b>Назначен:</b> <i>{task.get('assigned')}</i>\n" \
              f"Описание: {task.get('description')}\n" \
              f"Статус: {task.get('status')}\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Выбери группу"
        btn = get_group_list()
        kb = create_kbd(btn[0], btn[1], column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SELECT_USER
    elif cb == BTN_BACK[1]:
        update.callback_query.data = context.bot_data['status']
        return show_episode(update, context)


def select_user(update, context):
    groups = get_group_list()[1]
    if update.callback_query.data == BTN_BACK[1]:
        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data.get('TASK_NUM')
        return edit_episode(update, context)
    elif update.callback_query.data in groups:
        context.bot_data['users_group'] = update.callback_query.data
        users = get_users_in_group(update.callback_query.data, task_cnt=False)
        u_name = users[0]
        u_login = users[1]
        users_dict = {}
        i = 0
        for user in u_name:
            users_dict[u_login[i]] = u_name[i]
            i += 1
        context.bot_data['users'] = users_dict
        users[0].append(BTN_BACK[0])
        users[1].append(BTN_BACK[1])
        # context.bot_data['user_list'] = users[1][:-1]
        kb = create_kbd(users[0], users[1], column=2)
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"<b>Назначен:</b> <i>{task.get('assigned')}</i>\n" \
              f"Описание: {task.get('description')}\n" \
              f"Статус: {task.get('status')}\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Выбери пользователя"
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return ASK_SAVE_TASK_ASSIGNED


def ask_save_task_assigned(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_BACK[1]:
        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = BTN_ASSIGNED[1] # context.bot_data.get('TASK_NUM')
        return selected_edit_task_button(update, context)
    else:
        users = context.bot_data.get('users')
        s_u = users.get(update.callback_query.data)
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"<b>Назначен:</b> <i>{task.get('assigned')}</i>\n" \
              f"Описание: {task.get('description')}\n" \
              f"Статус: {task.get('status')}\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Назначить {s_u}"
        context.bot_data['users'] = update.callback_query.data
        kb = create_kbd([BTN_SAVE[0], BTN_CANCEL[0]], [BTN_SAVE[1], BTN_CANCEL[1]], column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SAVE_TASK_ASSIGNED


def save_task_assigned(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_CANCEL[1]:
        update.callback_query.data = context.bot_data['status']
        return show_episode(update, context)
    else:
        update_selected_field('sthpw',
                              'task',
                              'code',
                              context.bot_data.get('TASK_NUM'),
                              'assigned',
                              context.bot_data.get('users'))
        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data['status']
        context.bot_data['TASK_DESCRIPTION'] = get_task(context.bot_data.get('TASK_NUM'))
        return show_episode(update, context)


def ask_save_task_status(update, context):
    cb = update.callback_query.data
    if cb == BTN_BACK[1]:
        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data.get('TASK_NUM')
        return edit_episode(update, context)
    else:
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
              f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"Описание: {task.get('description')}\n" \
              f"<b>Статус:</b> <i>{task.get('status')}</i>\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Сохранить новый статус '{cb}'"
        context.bot_data['saving_status'] = cb
        kb = create_kbd([BTN_SAVE[0], BTN_CANCEL[0]], [BTN_SAVE[1], BTN_CANCEL[1]], column=2)
        update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SAVE_TASK_NEW_STATUS


def save_task_new_status(update, context):
    if update.callback_query.data == BTN_CANCEL[1]:
        update.callback_query.data = context.bot_data['status']
        return show_episode(update, context)
    else:
        update_selected_field('sthpw',
                              'task',
                              'code',
                              context.bot_data.get('TASK_NUM'),
                              'status',
                              context.bot_data.get('saving_status'))
        update.callback_query.data = context.bot_data['status']
        context.bot_data['TASK_DESCRIPTION'] = get_task(context.bot_data.get('TASK_NUM'))
        return show_episode(update, context)


def change_spaces(source_str, character):
    import re
    regex = r"\s+"
    subst = character
    result = re.sub(regex, subst, source_str, 0)
    return result


def check_convert_date(date):
    day = date[0]
    month = date[1]
    year = date[2]
    if day not in DAYS:
        day = '01'
    else:
        if len(day) == 1:
            day = f'0{day}'
    for key, value in MONTHS.items():
        if month in value:
            month = key
    if len(month) == 1:
        month = f'0{month}'
    if len(year) == 2:
        year = f'20{year}'
    return f'{year}-{month}-{day}'


def get_today_str():
    if len(str(dt.today().month)) == 1:
        month = f"0{dt.today().month}"
    else:
        month = dt.today().month
    if len(str(dt.today().day)) == 1:
        day = f"0{dt.today().day}"
    else:
        day = dt.today().day
    return f"{dt.today().year}-{month}-{day}"


def select_bid_year(update: Update, context: CallbackContext):
    if update.callback_query:
        cb = update.callback_query.data
        if cb == BTN_BACK[1]:
            update.callback_query.message.text = context.bot_data.get('TASK_NUM')
            update.callback_query.data = context.bot_data.get('TASK_NUM')
            return edit_episode(update, context)
        elif update.callback_query.data == BTN_TODAY[1]:
            date = get_today_str().split('-')
            context.bot_data['YEAR'] = date[0]
            context.bot_data['MONTH'] = date[1]
            context.bot_data['DAY'] = date[2]
            update.callback_query.data = date[2]
            return ask_save_task_bid_start_2(update, context)
        elif cb in YEAR:
            context.bot_data['YEAR'] = cb
            task = context.bot_data.get('TASK_DESCRIPTION')
            if context.bot_data.get('BID_START_OR_END'):
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"<b>Начало:</b> <i>{task.get('bid_start_date')}</i>\n" \
                      f"Конец: {task.get('bid_end_date')}\n\n" \
                      f"<b>Год:</b> <u>{context.bot_data.get('YEAR')}</u>\n\n" \
                      f"Выбери месяц"
            else:
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"Начало: {task.get('bid_start_date')}\n" \
                      f"<b>Конец:</b> <i> {task.get('bid_end_date')}</i>\n\n" \
                      f"<b>Год:</b> <u>{context.bot_data.get('YEAR')}</u>\n\n" \
                      f"Выбери месяц"

            btn_name = MONTH_NAME + [BTN_TODAY[0], BTN_BACK[0]]
            btn_cb = MONTH_NUMBER + [BTN_TODAY[1], BTN_BACK[1]]
            kb = create_kbd(btn_name, btn_cb, column=3)
            update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SELECT_MONTH_FOR_TASK
    else:
        return ask_to_save_task_bid_start(update, context)


def get_day_abbr_and_day(year, month):
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    calendar.setfirstweekday(calendar.MONDAY)
    d_a = list(calendar.day_abbr)
    calen = calendar.monthcalendar(year, month)
    cal = []
    for c in calen:
        cal = cal + c
    result = []
    index = 0
    for c in cal:
        if c != 0:
            result.append(f"{d_a[index]}:{c}")
        index += 1
        if index >= 7:
            index = 0
    return result


def select_month_for_task(update: Update, context: CallbackContext):
    if update.callback_query:
        if update.callback_query.data == BTN_BACK[1]:
            update.callback_query.data = BTN_BID_START[1]
            return selected_edit_task_button(update, context)
        elif update.callback_query.data == BTN_TODAY[1]:
            date = get_today_str().split('-')
            context.bot_data['YEAR'] = date[0]
            context.bot_data['MONTH'] = date[1]
            context.bot_data['DAY'] = date[2]
            update.callback_query.data = date[2]
            return ask_save_task_bid_start_2(update, context)
        else:
            month = context.bot_data['MONTH'] = update.callback_query.data
            year = context.bot_data['YEAR']
            task = context.bot_data.get('TASK_DESCRIPTION')
            if context.bot_data.get('BID_START_OR_END'):
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"<b>Начало:</b> <i>{task.get('bid_start_date')}</i>\n" \
                      f"Конец: {task.get('bid_end_date')}\n\n" \
                      f"<b>Год:</b> <u>{context.bot_data.get('YEAR')}</u>\n" \
                      f"<b>Месяц:</b> <u>{context.bot_data.get('MONTH')}</u>\n" \
                      f"\nВыбери дату"
            else:
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"Начало: {task.get('bid_start_date')}\n" \
                      f"<b>Конец:</b> <i> {task.get('bid_end_date')}</i>\n\n" \
                      f"<b>Год:</b> <u>{context.bot_data.get('YEAR')}</u>\n" \
                      f"<b>Месяц:</b> <u>{context.bot_data.get('MONTH')}</u>\n" \
                      f"\nВыбери дату"

            day_cnt = calendar.monthrange(int(year), int(month))[1]
            days = [x for x in range(1, day_cnt+1)]
            btn_name = get_day_abbr_and_day(int(year), int(month)) + [BTN_TODAY[0], BTN_BACK[0]]
            btn_cb = days + [BTN_TODAY[1], BTN_BACK[1]]
            kb = create_kbd(btn_name, btn_cb, column=7)
            update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
            return ASK_SAVE_TASK_BID_START_2
    else:
        return ask_to_save_task_bid_start(update, context)


def ask_save_task_bid_start_2(update: Update, context: CallbackContext):
    if update.callback_query:
        if update.callback_query.data == BTN_BACK[1]:
            update.callback_query.data = context.bot_data['YEAR']
            return select_bid_year(update, context)
        elif update.callback_query.data == BTN_TODAY[1]:
            date = get_today_str().split('-')
            context.bot_data['YEAR'] = date[0]
            context.bot_data['MONTH'] = date[1]
            context.bot_data['DAY'] = date[2]
            update.callback_query.data = date[2]
            return ask_save_task_bid_start_2(update, context)
        else:
            task = context.bot_data.get('TASK_DESCRIPTION')
            context.bot_data['DAY'] = update.callback_query.data
            date = f"{context.bot_data.get('YEAR')}-{context.bot_data.get('MONTH')}-{context.bot_data.get('DAY')}"
            date_normal = f"{context.bot_data.get('DAY')}.{context.bot_data.get('MONTH')}.{context.bot_data.get('YEAR')}"
            if context.bot_data.get('BID_START_OR_END'):
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"<b>Начало:</b> <i>{task.get('bid_start_date')}</i>\n" \
                      f"Конец: {task.get('bid_end_date')}\n" \
                      f"\nСохранить новую дату: <b>{date_normal}</b>"
            else:
                msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                      f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                      f"Назначен: {task.get('assigned')}\n" \
                      f"Описание: {task.get('description')}\n" \
                      f"Статус: {task.get('status')}\n" \
                      f"Начало: {task.get('bid_start_date')}\n" \
                      f"<b>Конец:</b> <i> {task.get('bid_end_date')}</i>\n" \
                      f"\nСохранить новую дату: <b>{date_normal}</b>"

            kb = create_kbd([BTN_SAVE[0], BTN_CANCEL[0]], [BTN_SAVE[1], BTN_CANCEL[1]], column=2)
            context.bot_data['bid_start'] = f"{date} {datetime.datetime.now().strftime('%H:%M:%S')}"
            update.callback_query.edit_message_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
            return SAVE_TASK_BID_START
    else:
        ask_to_save_task_bid_start(update, context)


def ask_to_save_task_bid_start(update: Update, context: CallbackContext):
    if update.callback_query:
        if update.callback_query.data == BTN_BACK[1]:
            update.callback_query.message.text = context.bot_data.get('TASK_NUM')
            update.callback_query.data = context.bot_data.get('TASK_NUM')
            return edit_episode(update, context)
    else:
        cb = update.message.text
        cb = cb.replace(',', ' ').replace('_', ' ').replace('.', ' ')
        cb = change_spaces(cb, '.').split('.')
        date = check_convert_date(cb)
        task = context.bot_data.get('TASK_DESCRIPTION')

        context.bot_data['YEAR'] = date.split('-')[0]
        context.bot_data['MONTH'] = date.split('-')[1]
        context.bot_data['DAY'] = date.split('-')[2]
        date_normal = f"{context.bot_data.get('DAY')}.{context.bot_data.get('MONTH')}.{context.bot_data.get('YEAR')}"

        if context.bot_data.get('BID_START_OR_END'):
            msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                  f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                  f"Назначен: {task.get('assigned')}\n" \
                  f"Описание: {task.get('description')}\n" \
                  f"Статус: {task.get('status')}\n" \
                  f"<b>Начало:</b> <i>{task.get('bid_start_date')}</i>\n" \
                  f"Конец: {task.get('bid_end_date')}\n\n" \
                  f"Сохранить новую дату: '{date_normal}'"
        else:
            msg = f"{get_scene_msg(context.bot_data.get('SCENE_DATA'))}\n" \
                  f"\nЗадача №{context.bot_data.get('TASK_NUM')}\n" \
                  f"Назначен: {task.get('assigned')}\n" \
                  f"Описание: {task.get('description')}\n" \
                  f"Статус: {task.get('status')}\n" \
                  f"Начало: {task.get('bid_start_date')}\n" \
                  f"<b>Конец:</b> <i> {task.get('bid_end_date')}</i>\n\n" \
                  f"Сохранить новую дату: '{date_normal}'"

        context.bot_data['bid_start'] = f"{date} {datetime.datetime.now().strftime('%H:%M:%S')}"
        context.bot.deleteMessage(message_id=update.message.message_id - 1, chat_id=update.message.chat_id)
        context.bot.deleteMessage(message_id=update.message.message_id, chat_id=update.message.chat_id)
        kb = create_kbd([BTN_SAVE[0], BTN_CANCEL[0]], [BTN_SAVE[1], BTN_CANCEL[1]], column=2)
        update.message.reply_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SAVE_TASK_BID_START


def save_bid_start(update, context):
    if update.callback_query.data == BTN_CANCEL[1]:
        update.callback_query.data = context.bot_data['status']
        return show_episode(update, context)
    else:
        if context.bot_data.get('BID_START_OR_END'):
            update_selected_field('sthpw',
                                  'task',
                                  'code',
                                  context.bot_data.get('TASK_NUM'),
                                  'bid_start_date',
                                  context.bot_data.get('bid_start'))
        else:
            update_selected_field('sthpw',
                                  'task',
                                  'code',
                                  context.bot_data.get('TASK_NUM'),
                                  'bid_end_date',
                                  context.bot_data.get('bid_start'))

        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data['status']
        context.bot_data['TASK_DESCRIPTION'] = get_task(context.bot_data.get('TASK_NUM'))
        return show_episode(update, context)


def update_selected_field(project_name, table, filtered_field, filtered_data, updated_field, updated_data):
    Batch(project_name)
    update = Update()
    update.set_table(table)
    update.add_filter(filtered_field, f"'{filtered_data}'")
    db_res = DbResource.get_default(project_name)
    update.db_resource = db_res
    data = {updated_field: updated_data}
    update.data = data
    query = update.get_statement()
    sql1 = DbContainer.get(update.db_resource)
    sql1.query = query
    update.sql = sql1
    sql1.do_update(query)


def ask_to_save_task_description(update: Update, context: CallbackContext):
    if update.callback_query:
        if update.callback_query.data == BTN_BACK[1]:
            update.callback_query.message.text = context.bot_data.get('TASK_NUM')
            update.callback_query.data = context.bot_data.get('TASK_NUM')
            return edit_episode(update, context)
    else:
        task = context.bot_data.get('TASK_DESCRIPTION')
        msg = f"Задача №{context.bot_data.get('TASK_NUM')}\n" \
              f"Назначен: {task.get('assigned')}\n" \
              f"<b>Описание:</b> <i>{task.get('description')}</i>\n" \
              f"Начало: {task.get('bid_start_date')}\n" \
              f"Конец: {task.get('bid_end_date')}\n\n" \
              f"Сохранить новое описание: '{update.message.text}'"
        context.bot_data['task_description'] = update.message.text
        context.bot.deleteMessage(message_id=update.message.message_id - 1, chat_id=update.message.chat_id)
        context.bot.deleteMessage(message_id=update.message.message_id, chat_id=update.message.chat_id)
        kb = create_kbd([BTN_SAVE[0], BTN_CANCEL[0]], [BTN_SAVE[1], BTN_CANCEL[1]], column=2)
        update.message.reply_text(text=msg, parse_mode=telegram.ParseMode.HTML, reply_markup=kb)
        return SAVE_TASK_DESCRIPTION


def save_description(update: Update, context: CallbackContext):
    if update.callback_query.data == BTN_CANCEL[1]:
        update.callback_query.data = context.bot_data['status']
        return show_episode(update, context)
    else:
        update_selected_field('sthpw',
                              'task',
                              'code',
                              context.bot_data.get('TASK_NUM'),
                              'description',
                              context.bot_data.get('task_description'))
        update.callback_query.message.text = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data.get('TASK_NUM')
        update.callback_query.data = context.bot_data['status']
        context.bot_data['TASK_DESCRIPTION'] = get_task(context.bot_data.get('TASK_NUM'))
        return show_episode(update, context)


def search_assets(update: Update, context: CallbackContext):
    def get_count(prc, status):
        return len(Search.eval(f"@SOBJECT(sthpw/task['process', '{prc}']['status', '{status}'])"))

    if update.callback_query.data == BTN_BACK[1]:
        return m_menu(update, context)
    elif update.callback_query.data == 'show_all':
        print('Show all')
    elif update.callback_query.data == 'search':
        print('Search')
    else:
        btn_name = ['Показать всё', 'Поиск']
        call_data = ['show_all', 'search']
        pipelines = get_pipeline_process('dolly3d/assets')
        task_pipeline = ''
        for pipeline in pipelines:
            if update.callback_query.data == pipeline.get_name():
                task_pipeline = pipeline.get_task_pipeline()
        pipelines = get_pipeline_process(task_pipeline)
        for process in pipelines:
            btn_name.append(f"{process.get_name()} | {get_count(update.callback_query.data, process.get_name())}")
            call_data.append(process.get_name())
        msg = 'Выбери статус'
        btn_name.append(BTN_BACK[0])
        call_data.append(BTN_BACK[1])
        kb = create_kbd(btn_name, call_data, column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TST_ASSETS


def tst_assets(update: Update, context: CallbackContext):
    cd = update.callback_query.data
    if cd == BTN_BACK[1]:
        update.callback_query.data = 'Asset'
        return search_menu(update, context)


def search_users(update: Update, context: CallbackContext):
    groups = get_group_list()[1]
    if update.callback_query.data == BTN_BACK[1]:
        return m_menu(update, context)
    elif update.callback_query.data in groups:
        context.bot_data['users_group'] = update.callback_query.data
        users = get_users_in_group(update.callback_query.data)
        users[0].append(BTN_BACK[0])
        users[1].append(BTN_BACK[1])
        context.bot_data['user_list'] = users[1][:-1]
        kb = create_kbd(users[0], users[1])
        msg = 'Выбери пользователя'
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SHOW_USERS


def get_task_count_for_user(user):
    Batch()
    searches = Search('sthpw/task')
    searches.add_filter('assigned', f"{user}")
    return searches.get_count()


def get_task_for_user(user, limit=5, offset=0):
    Batch()
    tasks = []
    searches = Search('sthpw/task')
    searches.add_filter('assigned', f"{user}")
    searches.set_limit(limit)
    searches.set_offset(offset)
    search = searches.get_sobjects()
    for result in search:
        tmp_dict = result.get_sobject_dict()
        Batch(DEFAULT_PROJECT)
        s_obj = tmp_dict.get('search_type')
        exp = f"@SOBJECT({s_obj}['code', '{result.get('search_code')}'])"
        ep_desc = Search.eval(exp)
        if ep_desc:
            for ep in ep_desc:
                tmp_ep = ep.get_sobject_dict()
                if tmp_ep.get('name') != '':
                    tmp_dict['ep_name'] = tmp_ep.get('name')
                else:
                    tmp_dict['ep_name'] = ''
                if tmp_ep.get('description') != '':
                    tmp_dict['ep_description'] = ep.get_description()
                else:
                    tmp_dict['ep_description'] = ''
        else:
            tmp_dict['ep_description'] = ''
            tmp_dict['ep_name'] = ''
        tmp_dict['ep_ppl'] = tmp_ep.get('pipeline_code')
        tasks.append(tmp_dict)
    return tasks


def make_msg(tasks: []):
    message = str()
    rec = list()
    if tasks:
        for task in tasks:
            tmp_str = ''
            ep_name = task['ep_name']
            status = task['status']
            ep_description = task['ep_description']
            assigned = task['assigned']
            task_code = task['code']
            episode_code = task['search_code']
            if ep_name:
                tmp_str = tmp_str + f"#{ep_name.replace(' ', '_').replace('.', '_')} "
            if status:
                tmp_str = tmp_str + f"#{status.replace(' ', '_').replace('.', '_')}:\n"
            if ep_description:
                tmp_str = tmp_str + f"{ep_description}\n"
            if assigned:
                tmp_str = tmp_str + f"Исполнитель: {assigned}\n"
            if task_code:
                tmp_str = tmp_str + f"/{task_code}"
            if episode_code:
                tmp_str = tmp_str + f" /{episode_code}\n"
            rec.append(tmp_str)

        message = '\n\n'.join(rec)

    return message


def show_users(update: Update, context: CallbackContext):
    cd = update.callback_query.data
    if cd == BTN_BACK[1]:
        update.callback_query.data = 'Users'
        return search_menu(update, context)
    elif cd in context.bot_data.get('user_list'):
        context.bot_data['current_user'] = cd
        tasks = get_task_for_user(cd, limit=5, offset=0)
        context.bot_data['max_task'] = get_task_count_for_user(cd)
        context.bot_data['next_step'] = 5
        context.bot_data['prev_step'] = 0
        msg = make_msg(tasks)
        btn_next_cap = f"5 - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        if context.bot_data.get('max_task') <= LIMIT:
            kb = create_kbd([BTN_BACK[0]], [BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_next_cap, BTN_BACK[0]], [BTN_NEXT[1], BTN_BACK[1]], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_USER_NAVIGATION


def users_task_navigate(update: Update, context: CallbackContext):
    if update.message:
        print(update.message.text)
    elif update.callback_query.data == BTN_BACK[1]:
        update.callback_query.data = context.bot_data.get('users_group')
        return search_users(update, context)
    elif update.callback_query.data == BTN_NEXT:
        step = context.bot_data.get('next_step')
        tasks = get_task_for_user(context.bot_data.get('current_user'), limit=5, offset=step)
        context.bot_data['next_step'] = step + 5
        context.bot_data['prev_step'] = step - 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {[0]}"
        btn_prev_cap = f"{BTN_PREV[0]} {context.bot_data.get('prev_step')+5} - {context.bot_data.get('max_task')}"
        if context.bot_data['next_step'] >= context.bot_data['max_task']:
            kb = create_kbd([btn_prev_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_NEXT[1], BTN_BACK[1]], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
    elif update.callback_query.data == BTN_PREV[1]:
        step = context.bot_data.get('prev_step')
        tasks = get_task_for_user(context.bot_data.get('current_user'), limit=5, offset=step)
        context.bot_data['prev_step'] = step - 5
        context.bot_data['next_step'] = step + 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT[0]}"
        btn_prev_cap = f"{BTN_PREV[0]} {context.bot_data.get('prev_step')+5} - {context.bot_data.get('max_task')}"
        if context.bot_data['prev_step'] < 0:
            context.bot_data['prev_step'] = 0
            kb = create_kbd([btn_next_cap, BTN_BACK[0]], [BTN_NEXT[1], BTN_BACK[1]], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BTN_BACK[0]], [BTN_PREV[1], BTN_NEXT[1], BTN_BACK[1]], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_USER_NAVIGATION


def m_menu(update: Update, context: CallbackContext):
    cur_user = find_user(update.effective_user.id)
    if not cur_user[0]:
        create_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name)
        cur_user = find_user(update.effective_user.id)

    context.bot_data['login_in_group'] = cur_user[2]
    context.bot_data['started'] = 'yes'

    supervisor = ['supervisor', 'admin']
    mod_rig = ['modeller', 'rigger']

    if any(word in supervisor for word in context.bot_data.get('login_in_group')):
        kb = create_kbd(
            ['Эпизоды', 'Ассеты', 'Пользователи', 'Поиск'],
            ['Episodes', 'Asset', 'Users', 'search'])
    elif any(word in mod_rig for word in context.bot_data.get('login_in_group')):
        kb = create_kbd(['Ассеты', 'Поиск'], ['Assets', 'search'])
    else:
        kb = create_kbd(['Эпизоды', 'Поиск'], ['Episodes', 'search'])
    msg = 'Нажми на кнопку'
    update.callback_query.edit_message_text(text=msg, reply_markup=kb)
    return SEARCH_MENU


def sel_status(update: Update, context: CallbackContext):
    def get_data(user, datas):
        Batch(project_code=DEFAULT_PROJECT)
        exp = f"@SOBJECT(sthpw/task['assigned', '{user}']['status', '{datas}'].complex/scenes)"
        sobjects = Search.eval(exp)
        result = []
        if sobjects:
            for sobject in sobjects:
                result.append(sobject.get_data())
        return result

    data = update.callback_query.data
    username = update.effective_user.username
    msg = ''
    kb = create_kbd([BTN_BACK[0]], [BTN_BACK[1]], column=1)
    if data == BTN_BACK[1]:
        return m_menu(update, context)


def conv_date(datetimes: str):
    from datetime import date
    if datetimes:
        date_ = date(year=int(datetimes[:4]), month=int(datetimes[5:7]),
                     day=int(datetimes[8:10])).strftime('%d.%m.%Y')
        return date_ + ' ' + datetimes[11:19]
    else:
        return ' '


def episodes():
    results = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_menu)],
        states={
            MAIN_MENU: [CallbackQueryHandler(m_menu), CommandHandler('cancel', cancel)],
            SEARCH_MENU: [CallbackQueryHandler(search_menu), CommandHandler('cancel', cancel)],
            SEARCH_EPISODES: [CallbackQueryHandler(search_episodes), CommandHandler('cancel', cancel)],
            SEARCH_ASSETS: [CallbackQueryHandler(search_assets), CommandHandler('cancel', cancel)],
            SEARCH_USERS: [CallbackQueryHandler(search_users), CommandHandler('cancel', cancel)],
            SHOW_USERS: [CallbackQueryHandler(show_users), CommandHandler('cancel', cancel)],
            SHOW_EPISODE: [CallbackQueryHandler(show_episode), CommandHandler('cancel', cancel)],
            TST_ASSETS: [CallbackQueryHandler(tst_assets), CommandHandler('cancel', cancel)],
            TASK_USER_NAVIGATION: [CallbackQueryHandler(users_task_navigate), CommandHandler('cancel', cancel)],
            TASK_EPISODE_NAVIGATION: [CallbackQueryHandler(episode_task_navigate),
                                      MessageHandler(Filters.text | Filters.command, edit_episode),
                                      CommandHandler('cancel', cancel)],
            EDIT_TASK_DESCRIPTION: [CallbackQueryHandler(selected_edit_task_button),
                                    CommandHandler('cancel', cancel)],
            ASK_SAVE_TASK_STATUS: [CallbackQueryHandler(ask_save_task_status),
                                   CommandHandler('cancel', cancel)],
            SAVE_TASK_NEW_STATUS: [CallbackQueryHandler(save_task_new_status),
                                   CommandHandler('cancel', cancel)],
            SELECT_USER: [CallbackQueryHandler(select_user),
                          CommandHandler('cancel', cancel)],
            ASK_SAVE_TASK_ASSIGNED: [CallbackQueryHandler(ask_save_task_assigned),
                                     CommandHandler('cancel', cancel)],
            SAVE_TASK_ASSIGNED: [CallbackQueryHandler(save_task_assigned),
                                 CommandHandler('cancel', cancel)],
            TEST: [CallbackQueryHandler(test),
                                    CommandHandler('cancel', cancel)],
            ASK_SAVE_TASK_DESCRIPTION: [CallbackQueryHandler(ask_to_save_task_description),
                                        MessageHandler(Filters.text, ask_to_save_task_description),
                                        CommandHandler('cancel', cancel)],
            ASK_SAVE_TASK_BID_START: [CallbackQueryHandler(ask_to_save_task_bid_start),
                                      MessageHandler(Filters.text, ask_to_save_task_bid_start),
                                      CommandHandler('cancel', cancel)],
            SAVE_TASK_DESCRIPTION: [CallbackQueryHandler(save_description),CommandHandler('cancel', cancel)],
            SELECT_YEAR_FOR_TASK: [CallbackQueryHandler(select_bid_year),
                                   MessageHandler(Filters.text,select_bid_year),
                                   CommandHandler('cancel', cancel)],
            SELECT_MONTH_FOR_TASK: [CallbackQueryHandler(select_month_for_task),
                                    MessageHandler(Filters.text,select_month_for_task),
                                    CommandHandler('cancel', cancel)],
            ASK_SAVE_TASK_BID_START_2: [CallbackQueryHandler(ask_save_task_bid_start_2),
                                        MessageHandler(Filters.text, ask_to_save_task_bid_start),
                                        CommandHandler('cancel', cancel)],
            SAVE_TASK_BID_START: [CallbackQueryHandler(save_bid_start),
                                  CommandHandler('cancel', cancel)],
        },
        fallbacks=[ConversationHandler.END],
    )
    return results


def get_group(login):
    Batch()
    exp = f"@SOBJECT(sthpw/login['login','{login}'].sthpw/login_in_group)"
    result = Search.eval(exp)
    user_in_groups = []
    if result:
        for res in result:
            user_in_groups.append(res.get_value('login_group'))
        return user_in_groups
    else:
        return None


def find_user(user_id):
    Batch()
    exp = f"@SOBJECT(sthpw/login['phone_number','{user_id}'])"
    sobjects = Search.eval(exp)
    if len(sobjects) > 0:
        for sobject in sobjects:
            login = sobject.get_value('login')
        user_group = get_group(login)
        return [True, login, user_group]
    else:
        return [False, None, None]


def create_user(user_id, user_name, first_name, last_name):
    Batch('sthpw')
    insert = Insert()
    insert.set_table('login')
    db_res = DbResource.get_default('sthpw')
    insert.db_resource = db_res
    if last_name is None:
        data = {
            'code': user_name,
            'login': user_name,
            'upn': user_name,
            'first_name': first_name,
            'display_name': first_name,
            'phone_number': user_id}
        insert.data = data
    else:
        data = {
            'code': user_name,
            'login': user_name,
            'upn': user_name,
            'first_name': first_name,
            'last_name': last_name,
            'display_name': first_name + ' ' + last_name,
            'phone_number': user_id}
        insert.data = data
    query = insert.get_statement()
    sql1 = DbContainer.get(insert.db_resource)
    sql1.query = query
    insert.sql = sql1
    sql1.do_update(query)


def create_kbd(btn_name_lst, callback_data_lst, row=False, column=1):
    def build_menu(buttons, n_cols,
                   header_buttons=None,
                   footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            menu.append([footer_buttons])
        return menu

    kbd = []
    if not row:
        index = 0
        for btn in btn_name_lst:
            kbd.append(InlineKeyboardButton(btn, callback_data=callback_data_lst[index]))
            index += 1
        return InlineKeyboardMarkup(build_menu(kbd, column))
    elif row:
        index = 0
        for btn in btn_name_lst:
            kbd.append(InlineKeyboardButton(btn, callback_data=callback_data_lst[index]))
            index += 1
        return InlineKeyboardMarkup([kbd])


def alternative_start(update, context: CallbackContext):
    cur_user = find_user(update.effective_user.id)
    if not cur_user[0]:
        create_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name)
        cur_user = find_user(update.effective_user.id)

    context.bot_data['login_in_group'] = cur_user[2]
    context.bot_data['started'] = 'yes'

    supervisor = ['supervisor', 'admin']
    mod_rig = ['modeller', 'rigger']

    if any(word in supervisor for word in context.bot_data.get('login_in_group')):
        kb = create_kbd(
            ['Эпизоды', 'Ассеты', 'Пользователи', 'Поиск'],
            ['Episodes', 'Asset', 'Users', 'search'])
    elif any(word in mod_rig for word in context.bot_data.get('login_in_group')):
        kb = create_kbd(['Ассеты', 'Поиск'], ['Assets', 'search'])
    else:
        kb = create_kbd(['Эпизоды', 'Поиск'], ['Episodes', 'search'])
    msg = 'Нажми на кнопку'
    update.message.reply_text(text=msg, reply_markup=kb)


def kill_all_conv(update: Update, context: CallbackContext):
    all_hand = context.dispatcher.handlers
    for dict_group in all_hand:
        handler: Handler
        for handler in all_hand[dict_group]:
            if isinstance(handler, ConversationHandler):
                handler._update_state(ConversationHandler.END, handler._get_key(update))


def helps(update: Update, context: CallbackContext):
    msg = f"Привет, {update.effective_user.username}, воспользуйся кнопками."
    update.message.reply_text(text=msg)


def echo(update: Update, context: CallbackContext):
    update.message.reply_text(text='Я тебя непонял воспользуйся кнопками. :-(')


def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update.message:
        update.message.reply_text(text=MY_ERROR_MESSAGE)
    else:
        update.callback_query.message.reply_text(text=MY_ERROR_MESSAGE)


def cancel(update: Update, context: CallbackContext):
    message = 'В следующий раз.'
    if update.message:
        update.message.reply_text(text=message)
    else:
        update.callback_query.edit_message_text(text=message)
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", alternative_start))
    dispatcher.add_handler(CommandHandler("help", helps))
    dispatcher.add_handler(episodes())
    dispatcher.add_handler(MessageHandler(Filters.all, echo))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

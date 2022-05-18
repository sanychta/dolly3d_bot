import logging
# import telegram
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler,
                          CallbackContext, Handler)
from telegram import (ReplyKeyboardMarkup, Update)
import tacticenv
# from os import path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pyasm.security import Batch
from pyasm.search import Search, SearchKey
# from pyasm.biz.pipeline import Process
# from pyasm.biz import Pipeline
# from pyasm.common import Container, Base, Xml, Environment, Common, XmlException
# from tactic_client_lib import TacticServerStub
# import configparser
from pprint import pprint

TOKEN = "2120442827:AAFS8L5w82bjoGI3k8YSTvcdcEW8-MiGuEY"

DEFAULT_PROJECT = 'dolly3d'
BACK = 'Назад'
EPISODES = 'complex/scenes'

MY_ERROR_MESSAGE = 'Обратитесь к разработчику - sanycht@gmail.com'

BTN_ADD = 'Добавить'
BTN_VIEW = 'Просмотр'
BTN_CANCEL_CAPTION = '🚫Отмена'
BTN_BACK_CAPTION = '⬅Назад'
BTN_YES_CAPTION = '✅Да'
BTN_NO_CAPTION = '❎Нет'
BTN_TICKET_CAPTION = 'Ticket-ы'
BTN_BUG_CAPTION = 'Bug-и'
CHECK = '✔'
BTN_NEXT = '▶'
BTN_PREV = '◀'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

(MAIN_MENU, SEARCH_MENU, SELECTED_BUTTON, SELECTED_RECORD, SEARCH_EPISODES, SEARCH_ASSETS, SEARCH_USERS,
 SHOW_USERS, SHOW_EPISODE, TST_ASSETS, TASK_USER_NAVIGATION, TASK_EPISOD_NAVIGATION) = range(12)


# def tst(update: Update, context: CallbackContext):
#     def get_sobject_dict(sobject):
#         search_key = SearchKey.get_by_sobject(sobject, use_id=False)
#         sobj = sobject.get_data()
#         sobj['__search_key__'] = search_key
#         return sobj
#
#     def get_data():
#         Batch()
#
#         search = Search('sthpw/pipeline')
#         search.add_op('begin')
#         search.add_filter(name='name', value='Episodes')
#
#         stypes_pipelines = search.get_sobjects()
#         # process = Process
#
#         for pipeline in stypes_pipelines:
#             for process in pipeline.get_process_names():
#                 print(f'{pipeline.get_name()}: "{process}"')
#                 xml = pipeline.get_pipeline_xml()
#                 print(xml.get_value("label").to_string())
#
#     msg = 'Выбери статус'
#     get_data()
#     kb = create_kbd(
#         [READY_TO_GO, ASSIGNED, AT_WORK, ON_PAUSE, NEED_HELP, REVISION, REJECTED, UNDER_REVIEW, ACCEPTED, PAID, BACK],
#         [READY_TO_GO, ASSIGNED, AT_WORK, ON_PAUSE, NEED_HELP, REVISION, REJECTED, UNDER_REVIEW, ACCEPTED, PAID, BACK],
#         column=2)
#     if not update.callback_query:
#         update.message.reply_text(text=msg, reply_markup=kb)
#     else:
#         update.callback_query.edit_message_text(text=msg, reply_markup=kb)
#     return SELECTED_BUTTON


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
    btn_name.append(BACK)
    call_data.append(BACK)
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
    btn_name.append(BACK)
    call_data.append(BACK)
    return [btn_name, call_data]


def get_users_in_group(group):
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
            user_name.append(f"{res.get_value('display_name')} | {get_count(res.get_value('code'))}")
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
    return len(Search.eval(f"@SOBJECT(sthpw/task['process', '{process}']['status', '{status}'])"))


def search_episodes(update: Update, context: CallbackContext):
    if update.callback_query.data == BACK:
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
        pipelines = get_pipeline_process(task_pipeline)
        for process in pipelines:
            btn_name.append(f"{process.get_name()} | {get_task_count_for_episodes(cd_process, process.get_name())}")
            call_data.append(process.get_name())
        msg = 'Выбери статус'
        btn_name.append(BACK)
        call_data.append(BACK)
        kb = create_kbd(btn_name, call_data, column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return SHOW_EPISODE


def get_task_for_episodes(process, status, limit=5, offset=0):
    Batch()
    tasks = []
    searches = Search('sthpw/task')
    searches.add_op('begin')
    searches.add_filter('process', f"{process}")
    searches.add_filter('status', f"{status}")
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
                if tmp_ep.get('description') != '':
                    tmp_dict['ep_description'] = ep.get_description()
                else:
                    tmp_dict['ep_description'] = 'None'
        else:
            tmp_dict['ep_description'] = 'No scenes for this task'
        tmp_dict['ep_ppl'] = tmp_ep.get('pipeline_code')
        tasks.append(tmp_dict)
    return tasks


def show_episode(update: Update, context: CallbackContext):
    if update.callback_query.data == BACK:
        update.callback_query.data = 'Episodes'
        return search_menu(update, context)
    else:
        context.bot_data['status'] = update.callback_query.data
        process = context.bot_data.get('process')
        status = update.callback_query.data
        tasks = get_task_for_episodes(process, status, limit=5, offset=0)
        context.bot_data['max_task'] = get_task_count_for_episodes(process, status)
        context.bot_data['next_step'] = 5
        context.bot_data['prev_step'] = 0
        msg = make_msg(tasks)
        btn_next_cap = f"5 - {context.bot_data.get('max_task')} {BTN_NEXT}"
        kb = create_kbd([btn_next_cap, BACK], [BTN_NEXT, BACK], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISOD_NAVIGATION


def episode_task_navigate(update: Update, context: CallbackContext):
    process = context.bot_data.get('process')
    status = context.bot_data.get('status')
    if update.callback_query.data == BACK:
        update.callback_query.data = context.bot_data.get('process')
        return search_episodes(update, context)
    elif update.callback_query.data == BTN_NEXT:
        step = context.bot_data.get('next_step')
        tasks = get_task_for_episodes(process, status, limit=5, offset=step)
        context.bot_data['next_step'] = step + 5
        context.bot_data['prev_step'] = step - 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT}"
        btn_prev_cap = f"{BTN_PREV} {context.bot_data.get('prev_step') + 5} - {context.bot_data.get('max_task')}"
        if context.bot_data['next_step'] >= context.bot_data['max_task']:
            kb = create_kbd([btn_prev_cap, BACK], [BTN_PREV, BACK], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISOD_NAVIGATION
    elif update.callback_query.data == BTN_PREV:
        step = context.bot_data.get('prev_step')
        tasks = get_task_for_episodes(process, status, limit=5, offset=step)
        context.bot_data['prev_step'] = step - 5
        context.bot_data['next_step'] = step + 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT}"
        btn_prev_cap = f"{BTN_PREV} {context.bot_data.get('prev_step') + 5} - {context.bot_data.get('max_task')}"
        if context.bot_data['prev_step'] < 0:
            context.bot_data['prev_step'] = 0
            kb = create_kbd([btn_next_cap, BACK], [BTN_NEXT, BACK], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        msg = make_msg(tasks)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_EPISOD_NAVIGATION


def search_assets(update: Update, context: CallbackContext):
    def get_count(process, status):
        return len(Search.eval(f"@SOBJECT(sthpw/task['process', '{process}']['status', '{status}'])"))

    if update.callback_query.data == BACK:
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
        btn_name.append(BACK)
        call_data.append(BACK)
        kb = create_kbd(btn_name, call_data, column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TST_ASSETS


def tst_assets(update: Update, context: CallbackContext):
    if update.callback_query.data == BACK:
        update.callback_query.data = 'Asset'
        return search_menu(update, context)


def search_users(update: Update, context: CallbackContext):
    groups = get_group_list()[1]
    if update.callback_query.data == BACK:
        return m_menu(update, context)
    elif update.callback_query.data in groups:
        users = get_users_in_group(update.callback_query.data)
        users[0].append(BACK)
        users[1].append(BACK)
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
                if tmp_ep.get('description') != '':
                    tmp_dict['ep_description'] = ep.get_description()
                else:
                    tmp_dict['ep_description'] = 'None'
        else:
            tmp_dict['ep_description'] = 'No scenes for this task'
        tmp_dict['ep_ppl'] = tmp_ep.get('pipeline_code')
        tasks.append(tmp_dict)
    return tasks


def make_msg(tasks: []):
    message = str()
    rec = list()
    tmp_str = str()
    if tasks:
        for task in tasks:
            tmp_str = ''
            if task['process']:
                tmp_str = tmp_str + f"#{task['process']}: "
            if task['status']:
                tmp_str = tmp_str + f"#{task['status']}:\n"
            if task['search_code']:
                tmp_str = tmp_str + f"Episode code: #{task['search_code']}\n"
            if task['ep_description']:
                tmp_str = tmp_str + f"Episode description: {task['ep_description']}\n"
            if task['bid_start_date']:
                tmp_str = tmp_str + f"Bid start: {conv_date(task['bid_start_date'])}\n"
            if task['bid_end_date']:
                tmp_str = tmp_str + f"Bid end: {conv_date(task['bid_end_date'])}\n"
            if task['description']:
                tmp_str = tmp_str + f"Task description: {task['description']}\n"
            if task['code']:
                tmp_str = tmp_str + f"Edit: #{task['code']}"
            rec.append(tmp_str)

        message = '\n\n'.join(rec)

    return message


def show_users(update: Update, context: CallbackContext):
    cd = update.callback_query.data
    if cd == BACK:
        update.callback_query.data = 'Users'
        return search_menu(update, context)
    elif cd in context.bot_data.get('user_list'):
        context.bot_data['current_user'] = cd
        tasks = get_task_for_user(cd, limit=5, offset=0)
        context.bot_data['max_task'] = get_task_count_for_user(cd)
        context.bot_data['next_step'] = 5
        context.bot_data['prev_step'] = 0
        msg = make_msg(tasks)
        btn_next_cap = f"5 - {context.bot_data.get('max_task')} {BTN_NEXT}"
        kb = create_kbd([btn_next_cap, BACK], [BTN_NEXT, BACK], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_USER_NAVIGATION


def users_task_navigate(update: Update, context: CallbackContext):
    if update.callback_query.data == BACK:
        update.callback_query.data = 'Users'
        return search_menu(update, context)
    elif update.callback_query.data == BTN_NEXT:
        step = context.bot_data.get('next_step')
        tasks = get_task_for_user(context.bot_data.get('current_user'), limit=5, offset=step)
        context.bot_data['next_step'] = step + 5
        context.bot_data['prev_step'] = step - 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT}"
        btn_prev_cap = f"{BTN_PREV} {context.bot_data.get('prev_step')+5} - {context.bot_data.get('max_task')}"
        if context.bot_data['next_step'] >= context.bot_data['max_task']:
            kb = create_kbd([btn_prev_cap, BACK], [BTN_PREV, BACK], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        msg = make_msg(tasks)
        # kb = create_kbd([BTN_PREV, BTN_NEXT, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_USER_NAVIGATION
    elif update.callback_query.data == BTN_PREV:
        step = context.bot_data.get('prev_step')
        tasks = get_task_for_user(context.bot_data.get('current_user'), limit=5, offset=step)
        context.bot_data['prev_step'] = step - 5
        context.bot_data['next_step'] = step + 5
        btn_next_cap = f"{context.bot_data.get('next_step')} - {context.bot_data.get('max_task')} {BTN_NEXT}"
        btn_prev_cap = f"{BTN_PREV} {context.bot_data.get('prev_step')+5} - {context.bot_data.get('max_task')}"
        if context.bot_data['prev_step'] < 0:
            context.bot_data['prev_step'] = 0
            kb = create_kbd([btn_next_cap, BACK], [BTN_NEXT, BACK], column=2)
        else:
            kb = create_kbd([btn_prev_cap, btn_next_cap, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        msg = make_msg(tasks)
        # kb = create_kbd([BTN_PREV, BTN_NEXT, BACK], [BTN_PREV, BTN_NEXT, BACK], column=2)
        update.callback_query.edit_message_text(text=msg, reply_markup=kb)
        return TASK_USER_NAVIGATION


def m_menu(update: Update, context: CallbackContext):
    cur_user = find_user(update.effective_user.id)
    if not cur_user[0]:
        create_user(
            tactic_srv,
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
    kb = create_kbd([BACK], [BACK], column=1)
    if data == BACK:
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
            SELECTED_BUTTON: [CallbackQueryHandler(sel_status), CommandHandler('cancel', cancel)],
            SHOW_USERS: [CallbackQueryHandler(show_users), CommandHandler('cancel', cancel)],
            SHOW_EPISODE: [CallbackQueryHandler(show_episode), CommandHandler('cancel', cancel)],
            TST_ASSETS: [CallbackQueryHandler(tst_assets), CommandHandler('cancel', cancel)],
            TASK_USER_NAVIGATION: [CallbackQueryHandler(users_task_navigate), CommandHandler('cancel', cancel)],
            TASK_EPISOD_NAVIGATION: [CallbackQueryHandler(episode_task_navigate), CommandHandler('cancel', cancel)],
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


def insert_record(server, stype, insert_data):
    server.insert(stype, insert_data)


def update_rec(server, stype, field, code, data):
    search_key = server.build_search_key(stype, code, project_code=DEFAULT_PROJECT)
    value = {field: data}
    server.update(search_key, value)


def create_user(server, user_id, user_name, first_name, last_name):
    server.set_project('sthpw')
    search_type = "sthpw/login"
    if last_name is None:
        data = {
            'code': user_name,
            'login': user_name,
            'upn': user_name,
            'first_name': first_name,
            'display_name': first_name,
            'phone_number': user_id}
    else:
        data = {
            'code': user_name,
            'login': user_name,
            'upn': user_name,
            'first_name': first_name,
            'last_name': last_name,
            'display_name': first_name + ' ' + last_name,
            'phone_number': user_id}
    server.insert(search_type, data)


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
            tactic_srv,
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
    # dispatcher.add_handler(gen_cfg_file())
    dispatcher.add_handler(episodes())
    dispatcher.add_handler(MessageHandler(Filters.all, echo))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

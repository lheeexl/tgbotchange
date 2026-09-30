from aiogram.fsm.state import State, StatesGroup

class ChangeForm(StatesGroup):
    title = State()
    description = State()
    reason = State()
    affected_area = State()
    priority = State()
    schedule_impact = State()
    cost_impact = State()
    responsible_person = State()
    comment = State()
    confirmation = State()

class EditChangeForm(StatesGroup):
    title = State()
    description = State()
    reason = State()
    affected_area = State()
    priority = State()
    schedule_impact = State()
    cost_impact = State()
    responsible_person = State()
    comment = State()

class StatusForm(StatesGroup):
    status = State()
    comment = State()

class SearchForm(StatesGroup):
    id = State()
    title = State()

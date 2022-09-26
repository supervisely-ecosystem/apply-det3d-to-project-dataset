import supervisely as sly
import sly_globals as g

def init(data, state):
    state["newProjName"] = f"{g.project_info.name} labeled"
    state["confThres"] = 0.3
    state["addMode"] = "replace"
    state["useDefaultInferenceParams"] = True
    state["applySW"] = {'X': False, 'Y': False, 'Z': False}
    state["applyCenterPTC"] = {'X': False, 'Y': False, 'Z': False}
    state["allowSW"] = {'X': False, 'Y': False, 'Z': False}
    state["disabledCenter"] = {'X': False, 'Y': False, 'Z': False}
    state["idx_to_change"] = 'X'
    data["coords"] = ["X", "Y", "Z"]
    state["collapsed4"] = True
    state["disabled4"] = True
    data["done4"] = False


def restart(data, state):
    data["done4"] = False



@g.my_app.callback("change_sw")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def change_sw(api: sly.Api, task_id, context, state, app_logger):
    val_for_center = state["applySW"][state['idx_to_change']]
    disable_val = val_for_center
    if not state["applySW"][state['idx_to_change']]:
        if g.model_info["train_data_centered"] is None:
            val_for_center = False
        else:
            val_for_center = g.model_info["train_data_centered"][['X', 'Y', 'Z'].index(state["idx_to_change"])]
    fields = [
        {"field": f"state.applyCenterPTC[{state['idx_to_change']}]", "payload": val_for_center},
        {"field": f"state.disabledCenter[{state['idx_to_change']}]", "payload": disable_val},
    ]
    g.api.app.set_fields(g.task_id, fields)


@g.my_app.callback("apply_parameters")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def apply_parameters(api: sly.Api, task_id, context, state, app_logger):
    g.finish_step(4)


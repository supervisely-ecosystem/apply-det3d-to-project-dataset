import supervisely as sly
import sly_globals as g


def init(data, state):
    state["newProjName"] = f"{g.project_info.name} labeled"
    state["confThres"] = 0.0
    state["addMode"] = "replace"
    state["collapsed4"] = True
    state["disabled4"] = True
    data["done4"] = False


def restart(data, state):
    data["done4"] = False



@g.my_app.callback("apply_parameters")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def apply_parameters(api: sly.Api, task_id, context, state, app_logger):
    g.finish_step(4)


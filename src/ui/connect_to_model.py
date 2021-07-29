import sly_globals as g
import supervisely_lib as sly


def init(data, state):
    state["connectionLoading"] = False
    data["modelInfo"] = {}
    data["connected"] = False
    data["connectionError"] = ""

    data["ssOptions"] = {
        "sessionTags": ["deployed_nn"],
        "showLabel": False,
        "size": "small"
    }

    data["done2"] = False

    state["activeStep"] = 2
    state["collapsed2"] = False
    state["disabled2"] = False


def restart(data, state):
    data['done2'] = False


@g.my_app.callback("connect")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def connect(api: sly.Api, task_id, context, state, app_logger):
    try:
        meta_json = g.api.task.send_request(state['sessionId'], "get_output_classes_and_tags", data={}) # TODO: timeouts (git pull)
        g.model_info = g.api.task.send_request(state['sessionId'], "get_session_info", data={})
        g.model_meta = sly.ProjectMeta.from_json(meta_json)
    except Exception as ex:
        fields = [
            {"field": "state.connectionLoading", "payload": False},
        ]
        g.api.app.set_fields(g.task_id, fields)
        app_logger.debug(ex)
        raise ConnectionError(f'cannot establish connection with model {state["sessionId"]}')

    fields = [
        {"field": "data.connected", "payload": True},
        {"field": "data.modelInfo", "payload": g.model_info},
    ]

    g.api.app.set_fields(g.task_id, fields)

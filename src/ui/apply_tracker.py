import sly_globals as g
import supervisely_lib as sly


def init(data, state):
    state["collapsed6"] = True
    state["disabled6"] = True
    data["done6"] = False

    data["resProjectId"] = None
    data["resProjectName"] = None
    data["started"] = False


@g.my_app.callback("apply_tracking")
@sly.timeit
def apply_tracking(api: sly.Api, task_id, context, state, app_logger):

    project_id = api.task.get_field(task_id, "data.resProjectId")
    dataset_id = api.dataset.get_list(project_id)[0]

    params = {"dataset_id": dataset_id.id}

    r = g.api.task.send_request(state["trackerSessionId"], "track_dataset", data=params)
    app_logger.info(r)
    fields = [
        {"field": "data.started", "payload": False},
        {"field": "data.done6", "payload": True}
    ]
    api.task.set_fields(task_id, fields)
    g.my_app.stop()

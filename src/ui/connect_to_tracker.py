import sly_globals as g
import supervisely_lib as sly


def init(data, state):
    data["ssTrackerOptions"] = {
        "sessionTags": ["sly_3d_tracking"],
        "showLabel": False,
        "size": "small"
    }
    state["collapsed5"] = True
    state["disabled5"] = True


@g.my_app.callback("connect_to_tracker")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def connect_to_tracker(api: sly.Api, task_id, context, state, app_logger):
    try:
        tracker_info = g.api.task.send_request(state['trackerSessionId'], "get_session_info", data={})
        app_logger.info(tracker_info)
        data = state['trackerSessionId']
    except Exception as ex:
        data = False
        raise ConnectionError(f'cannot establish connection with tracker {state["sessionId"]}')
    finally:
        fields = [
            {"field": "data.trackerTask", "payload": data},
            {"field": "state.trackerConnectionLoading", "payload": False},
        ]

    g.api.app.set_fields(g.task_id, fields)


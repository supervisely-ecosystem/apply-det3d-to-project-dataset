import supervisely_lib as sly
import sly_globals as g


def init(data, state):
    state["collapsed5"] = True
    state["disabled5"] = True
    data["done5"] = False

    data["resProjectId"] = None
    data["resProjectName"] = None
    data["started"] = False


@g.my_app.callback("apply_model")
@sly.timeit
def apply_model(api: sly.Api, task_id, context, state, app_logger):

    # Setup new project
    project_names = [x.name for x in api.project.get_list(g.workspace_id)]
    new_project_name = sly._utils.generate_free_name(used_names=project_names, possible_name=state["newProjName"])
    clone_task_id = api.project.clone(g.project_id, g.workspace_id, new_project_name)
    api.task.wait(clone_task_id, api.task.Status('finished'))  # TODO: progress bar for clone

    new_project = api.project.get_info_by_name(g.workspace_id, new_project_name)
    new_dataset = api.dataset.get_list(new_project.id)[0] # only first dataset


    pointclouds = api.pointcloud.get_list(new_dataset.id)

    params = {"pointcloud_ids": [p.id for p in pointclouds],
              "threshold": state["confThres"]}

    new_annotations = g.api.task.send_request(state['sessionId'], "inference_pointcloud_ids", data=params)
    new_annotations = new_annotations["results"]

    # update meta
    if state["addMode"] == "merge":
        res_project_meta = g.project_meta.merge(g.model_meta)
    elif state["addMode"] == "replace":
        res_project_meta = g.model_meta
        api.project.update_meta(new_project.id, sly.ProjectMeta)
    else:
        raise ValueError("Wrong add mode")

    api.project.update_meta(new_project.id, res_project_meta.to_json())

    for i, pc in enumerate(pointclouds):
        api.pointcloud.annotation.append(pc.id, sly.PointcloudAnnotation.from_json(new_annotations[i], res_project_meta))



    fields = [
        {"field": "data.resProjectId", "payload": new_project.id},
        {"field": "data.resProjectName", "payload": new_project.name},
        {"field": "data.started", "payload": False},
        {"field": "data.done5", "payload": True}
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_project(task_id, new_project.id, new_project.name)
    g.my_app.stop()

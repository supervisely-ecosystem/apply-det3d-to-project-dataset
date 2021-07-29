import os
import supervisely_lib as sly

my_app = sly.AppService()
api = my_app.public_api
task_id = my_app.task_id

owner_id = int(os.environ['context.userId'])
team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])

project_id = int(os.environ['modal.state.slyProjectId'])
project_info = api.project.get_info_by_id(project_id)
if project_info is None:  # for debug
    raise ValueError(f"Project with id={project_id} not found")

project_meta: sly.ProjectMeta = sly.ProjectMeta.from_json(my_app.public_api.project.get_meta(project_id))

model_info = None
model_meta: sly.ProjectMeta = None

def finish_step(step_num):
    next_step = step_num + 1
    fields = [
        {"field": f"data.done{step_num}", "payload": True},
        {"field": f"state.collapsed{next_step}", "payload": False},
        {"field": f"state.disabled{next_step}", "payload": False},
        {"field": f"state.activeStep", "payload": next_step},
    ]
    api.app.set_field(task_id, "data.scrollIntoView", f"step{next_step}")
    api.app.set_fields(task_id, fields)
import os
import sys
import pathlib
import supervisely as sly
from supervisely.app.v1.app_service import AppService
from dotenv import load_dotenv

root_source_path = str(pathlib.Path(os.path.abspath(sys.argv[0])).parents[1])
sly.logger.info(f"Root source directory: {root_source_path}")
sys.path.append(root_source_path)

source_path = str(pathlib.Path(sys.argv[0]).parents[0])
sly.logger.info(f"App source directory: {source_path}")
sys.path.append(source_path)

ui_sources_dir = os.path.join(source_path, "ui")
sly.logger.info(f"UI source directory: {ui_sources_dir}")
sys.path.append(ui_sources_dir)

# @TODO: for debug
debug_env_path = os.path.join(root_source_path, "debug.env")
# secret_debug_env_path = os.path.join(root_source_path, "secret_debug.env")
# load_dotenv(debug_env_path)
# load_dotenv(secret_debug_env_path, override=True)
if sly.is_development():
    load_dotenv(debug_env_path)
    load_dotenv(os.path.expanduser("~/supervisely.env"))


# owner_id = int(os.environ['context.userId'])
team_id = int(os.environ['context.teamId'])
project_id = int(os.environ['modal.state.slyProjectId'])
workspace_id = int(os.environ['context.workspaceId'])

my_app = AppService()
api = my_app.public_api
task_id = my_app.task_id

# @TODO: for debug
sly.fs.clean_dir(my_app.data_dir)

project_info = api.project.get_info_by_id(project_id)
if project_info is None:  # for debug
    raise ValueError(f"Project with id={project_id} not found")

project_meta: sly.ProjectMeta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))

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
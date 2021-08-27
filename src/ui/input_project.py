import sly_globals as g
import supervisely_lib as sly

def init(data, state):
    data["projectId"] = g.project_info.id
    data["projectName"] = g.project_info.name
    data["projectItemsCount"] = g.project_info.items_count
    #data["projectPreviewUrl"] = ??? TODO: preview

    data["done1"] = False
    state["collapsed1"] = False
    g.finish_step(1)


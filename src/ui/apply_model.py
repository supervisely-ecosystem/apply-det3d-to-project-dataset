from typing import OrderedDict
from supervisely.video_annotation.key_id_map import KeyIdMap
from supervisely.pointcloud_annotation.pointcloud_object_collection import PointcloudObjectCollection
from supervisely.video_annotation.frame_collection import FrameCollection
from supervisely.video_annotation.video_tag_collection import VideoTagCollection
import supervisely as sly
import sly_globals as g
from supervisely.geometry.cuboid_3d import Cuboid3d, Vector3d
from tracker import PubTracker as Tracker
import os
import numpy as np


def init_progress(data, name):
    data[f"progress{name}"] = 0
    data[f"progressCurrent{name}"] = 0
    data[f"progressTotal{name}"] = 0


def init(data, state):
    state["collapsed5"] = True
    state["disabled5"] = True
    state["task"] = "det"
    state["tracking"] = "CenterTrack"
    state["uploading"] = False
    data["done5"] = False

    data["resProjectId"] = None
    data["resProjectName"] = None
    data["started"] = False
    init_progress(data, "Inference")


def turn_around(angle):
    if angle < 0:
        return np.pi + angle
    else:
        return -np.pi + angle

class Annotation:
    @staticmethod
    def pred_to_sly_geometry(labels, reverse=False):
        geometry = []
        for l in labels:
            x, y = l["translation"][0], l["translation"][1]
            z = l["z_trans"]
            dx, dy, dz = l["size"][0], l["size"][1], l["size"][2]
            yaw = l["rotation"]
            position = Vector3d(float(x), float(y), float(z * 0.5))

            if reverse:
                yaw = turn_around(yaw)

            rotation = Vector3d(0, 0, float(yaw))
            dimension = Vector3d(float(dx), float(dy), float(dz))
            g = Cuboid3d(position, rotation, dimension)
            geometry.append(g)
        return geometry

    @staticmethod
    def create_annotation(tracking, meta):
        id_to_objects = {}
        annotations = {"objects": [], "figures": {}}
        for ptc_id, preds in tracking.items():
            geometry_list = Annotation.pred_to_sly_geometry(preds)
            figures = []
            for pred, geometry in zip(preds, geometry_list):  # by object in point cloud
                if pred["tracking_id"] in id_to_objects.keys():
                    pcobj = id_to_objects[pred["tracking_id"]]
                else:
                    pcobj = sly.PointcloudObject(meta.get_obj_class(pred["tracking_name"]))
                    id_to_objects[pred["tracking_id"]] = pcobj
                figures.append(sly.PointcloudFigure(pcobj, geometry))
                # TODO: add tag confidence
            
            annotations["figures"][ptc_id] = figures
        
        annotations["objects"] = PointcloudObjectCollection(list(id_to_objects.values()))
        frames = []
        for frame_ind, (ptc_id, figures) in enumerate(annotations["figures"].items()):
            frames.append(sly.Frame(frame_ind, figures))
        ann = sly.PointcloudEpisodeAnnotation(
            frames_count=len(tracking), 
            objects=annotations["objects"], 
            frames=FrameCollection(frames), 
            tags=VideoTagCollection([]))
        return ann


def track(predictions):
    work_dir = g.my_app.data_dir
    # TODO: check value
    tracker = Tracker(max_age=3)

    result = OrderedDict()
    print("Begin Tracking\n")
    for ind, (ptc_id, preds) in enumerate(predictions.items()):
        if ind == 0: # first frame
            tracker.reset()

        # TODO: check value
        time_lag = 1.0

        outputs = tracker.step_centertrack(preds, time_lag)
        annos = []

        for item in outputs:
            if item['active'] == 0:
                continue 
            nusc_anno = {
                "ptc_id": ptc_id,
                "translation": item['translation'],
                "z_trans": item["z_trans"],
                "size": item['size'],
                "rotation": item['rotation'],
                "velocity": item['velocity'],
                "tracking_id": str(item['tracking_id']),
                "tracking_name": item['detection_name'],
                "tracking_score": item['detection_score'],
            }
            annos.append(nusc_anno)
        result.update({ptc_id: annos})

    print("Finish tracking.")
    os.makedirs(work_dir, exist_ok=True)

    return result


@g.my_app.callback("apply_model")
@sly.timeit
@g.my_app.ignore_errors_and_show_dialog_window()
def apply_model(api: sly.Api, task_id, context, state, app_logger):
    def _update_progress(progress, name):
        fields = [
            {"field": f"data.progress{name}", "payload": int(progress.current * 100 / progress.total)},
            {"field": f"data.progressCurrent{name}", "payload": progress.current},
            {"field": f"data.progressTotal{name}", "payload": progress.total},
        ]
        api.task.set_fields(task_id, fields)
    # Setup new project
    project_names = [x.name for x in api.project.get_list(g.workspace_id)]
    new_project_name = sly._utils.generate_free_name(used_names=project_names, possible_name=state["newProjName"])
    
    clone_task_id = api.project.clone(g.project_id, g.workspace_id, new_project_name)
    api.task.wait(clone_task_id, api.task.Status('finished')) # TODO: progress bar for clone

    old_dataset = api.dataset.get_list(g.project_id)[0]
    frames_to_names = api.pointcloud_episode.get_frame_name_map(old_dataset.id)
    names_to_frames = {v: k for k, v in frames_to_names.items()}

    new_project = api.project.get_info_by_name(g.workspace_id, new_project_name)
    new_dataset = api.dataset.get_list(new_project.id)[0] # TODO: only first dataset?

    if new_project.type == "point_cloud_episodes":
        pointclouds = api.pointcloud_episode.get_list(new_dataset.id)
    elif new_project.type == "point_clouds":
        pointclouds = api.pointcloud.get_list(new_dataset.id)
    
    frames_to_ptcs = {names_to_frames[ptc.name] : ptc.id for ptc in pointclouds}
    frames_to_ptcs = OrderedDict(frames_to_ptcs.items())
    frames_to_ptcs = OrderedDict(sorted(frames_to_ptcs.items(), key=lambda t: t[0]))
    pointcloud_ids = list(frames_to_ptcs.values())

    # update meta
    if state["addMode"] == "merge":
        res_project_meta = g.project_meta.merge(g.model_meta)
    elif state["addMode"] == "replace":
        res_project_meta = g.model_meta
        api.project.update_meta(new_project.id, sly.ProjectMeta().to_json())
    else:
        raise ValueError("Wrong add mode")

    api.project.update_meta(new_project.id, res_project_meta.to_json())
    
    progress = sly.Progress("Inference", len(pointcloud_ids), need_info_log=True)
    raw_results = OrderedDict()
    anns = OrderedDict()
    for ptc_ind, ptc_id in enumerate(pointcloud_ids):
        params = {
            "pointcloud_id": ptc_id,
            "threshold": state["confThres"],
            "classes": state["selectedClasses"],
            "project_type": new_project.type
        }
        result = g.api.task.send_request(state['sessionId'], "inference_pointcloud_id", data=params)
        try:
            result = result["results"]
        except KeyError:
            sly.logger.error("Something goes wrong and responce doesnt contain results")
            sly.logger.error(f"Results: {result}")
        raw_results[ptc_id] = result["raw_results"]
        anns[ptc_id] = result["annotation"]
        progress.iters_done_report(1)
        _update_progress(progress, "Inference")

    api.task.set_field(task_id, "state.uploading", True)
    if new_project.type == "point_clouds":
        for ptc_id in pointcloud_ids:
            api.pointcloud.annotation.append(
                ptc_id, 
                sly.PointcloudAnnotation.from_json(
                    anns[ptc_id], 
                    res_project_meta
                )
            )
    elif new_project.type == "point_cloud_episodes":
        if state["task"] == "det":
            objects = []
            frames = []
            
            for frame_ind, ptc_id in frames_to_ptcs.items():
                ann = sly.PointcloudAnnotation.from_json(anns[ptc_id], res_project_meta)
                objects.extend([obj for obj in ann.objects])
                frames.append(sly.Frame(frame_ind, ann.figures))
            
            objects = PointcloudObjectCollection(objects)
            annotation = sly.PointcloudEpisodeAnnotation(
                frames_count=len(anns),
                objects=objects, 
                frames=FrameCollection(frames), 
                tags=VideoTagCollection([]))
        elif state["task"] == "det_and_track":
            tracking = track(raw_results)
            annotation = Annotation.create_annotation(tracking, res_project_meta)
        uploaded_objects = KeyIdMap()
        api.pointcloud_episode.annotation.append(new_dataset.id,
                                                annotation,
                                                frames_to_ptcs,
                                                uploaded_objects)
    
    fields = [
        {"field": "data.resProjectId", "payload": new_project.id},
        {"field": "data.resProjectName", "payload": new_project.name},
        {"field": "data.started", "payload": False},
        {"field": "state.uploading", "payload": False},
        {"field": "data.done5", "payload": True}
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_project(task_id, new_project.id, new_project.name)
    g.my_app.stop()

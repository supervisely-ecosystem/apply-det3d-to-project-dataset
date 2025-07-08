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
from utils import clone_project


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
    data["resProjectPreviewUrl"] = g.project_info.image_preview_url
    data["started"] = False
    init_progress(data, "Inference")
    init_progress(data, "UploadAnns")


def turn_around(angle):
    if angle < 0:
        return np.pi + angle
    else:
        return -np.pi + angle


def get_cuboids_from_predictions(labels, reverse=False):
    geometry = []
    for l in labels:
        x, y = l["translation"][0], l["translation"][1]
        z = l["z_trans"]
        dx, dy, dz = l["size"][0], l["size"][1], l["size"][2]
        yaw = l["rotation"]
        position = Vector3d(float(x), float(y), float(z))

        if reverse:
            yaw = turn_around(yaw)

        rotation = Vector3d(0, 0, float(yaw))
        dimension = Vector3d(float(dx), float(dy), float(dz))
        g = Cuboid3d(position, rotation, dimension)
        geometry.append(g)
    return geometry


def get_objects_and_figures(predictions, meta):
    id_to_objects = {}
    figures = {}
    for ptc_id, preds in predictions.items():
        geometry_list = get_cuboids_from_predictions(preds)
        frame_figures = []
        for pred, geometry in zip(preds, geometry_list):  # by object in point cloud
            if pred["tracking_id"] in id_to_objects.keys():
                pcobj = id_to_objects[pred["tracking_id"]]
            else:
                pcobj = sly.PointcloudObject(meta.get_obj_class(pred["tracking_name"]))
                id_to_objects[pred["tracking_id"]] = pcobj
            frame_figures.append(sly.PointcloudFigure(pcobj, geometry))
            # TODO: add tag confidence
        
        figures[ptc_id] = frame_figures
    return list(id_to_objects.values()), figures


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
    progress = sly.Progress(f'Cloning {g.project_info.type} project', 1)
    sly.logger.info(f"Cloning {g.project_info.type} project")
    new_project = clone_project(
        api, 
        g.workspace_id, 
        g.project_id, 
        g.project_info.type,
        g.project_meta, 
        state["newProjName"], 
        state["addMode"] == "merge"
    )
    sly.logger.info(f"New project: '{new_project.name}' created")
    progress.iter_done_report()

    new_datasets = api.dataset.get_list(new_project.id)
    
    # update meta
    if state["addMode"] == "merge":
        res_project_meta = g.project_meta.merge(g.model_meta)
    elif state["addMode"] == "replace":
        res_project_meta = g.model_meta

    api.project.update_meta(new_project.id, res_project_meta.to_json())

    raw_results = {}
    anns = {}
    pointcloud_ids = {}
    frames_to_ptcs = {}
    ptcs_to_frames = {}
    progress = sly.Progress("Inference", sum(ds.items_count for ds in new_datasets), need_info_log=True)
    for dataset in new_datasets:
        if dataset.id not in raw_results.keys():
            raw_results[dataset.id] = OrderedDict()
        if dataset.id not in anns.keys():
            anns[dataset.id] = OrderedDict()
        pointclouds = api.pointcloud.get_list(dataset.id)
        names_to_ptcs = {ptc.name : ptc.id for ptc in pointclouds}
        names_to_ptcs = OrderedDict(names_to_ptcs.items())
        names_to_ptcs = OrderedDict(sorted(names_to_ptcs.items(), key=lambda t: t[0]))
        names_to_ptcs = OrderedDict(sorted(names_to_ptcs.items(), key=lambda t: t[0]))
        if new_project.type == str(sly.ProjectType.POINT_CLOUD_EPISODES):
            frames_to_ptcs[dataset.id] = OrderedDict({i: v for i, v in enumerate(names_to_ptcs.values())})
            ptcs_to_frames[dataset.id] = OrderedDict({v: k for k, v in frames_to_ptcs[dataset.id].items()})
        pointcloud_ids[dataset.id] = list(names_to_ptcs.values())
        
        for ptc_id in pointcloud_ids[dataset.id]:
            params = {
                "pointcloud_id": ptc_id,
                "threshold": state["confThres"],
                "classes": state["selectedClasses"],
                "project_type": new_project.type,
                "apply_sliding_window": state["applySW"],
                "center_ptc": state["applyCenterPTC"]
            }
            result = g.api.task.send_request(state['sessionId'], "inference_pointcloud_id", data=params, timeout=120)
            if "error" in result.keys():
                fields = [
                    {"field": "data.started", "payload": False},
                    {"field": "state.uploading", "payload": False}
                ]
                api.task.set_fields(task_id, fields)
                raise RuntimeError("Serving app failed: "+result["error"])
            result = result["results"]
            raw_results[dataset.id][ptc_id] = result["raw_results"]
            anns[dataset.id][ptc_id] = result["annotation"]
            progress.iter_done_report()
            _update_progress(progress, "Inference")
    
    anns_len = sum(ds.items_count for ds in new_datasets) if \
        new_project.type == str(sly.ProjectType.POINT_CLOUDS) else len(new_datasets)
    upload_anns_progress = sly.Progress("UploadAnns", anns_len, need_info_log=True)

    for dataset in new_datasets:
        api.task.set_field(task_id, "state.uploading", True)
        if new_project.type == str(sly.ProjectType.POINT_CLOUDS):
            for ptc_id in pointcloud_ids[dataset.id]:
                objects = []
                figures = []
                new_ann = sly.PointcloudAnnotation.from_json(anns[dataset.id][ptc_id], res_project_meta)
                objects.extend([obj for obj in new_ann.objects])
                figures.extend([fig for fig in new_ann.figures])
                objects = PointcloudObjectCollection(objects)
                result_ann = sly.PointcloudAnnotation(objects, figures, VideoTagCollection([]))
                api.pointcloud.annotation.append(ptc_id, result_ann)
                upload_anns_progress.iter_done_report()
                _update_progress(upload_anns_progress, "UploadAnns")
        elif new_project.type == str(sly.ProjectType.POINT_CLOUD_EPISODES):
            if state["task"] == "det":
                objects = []
                frames = []

                for frame_ind, ptc_id in frames_to_ptcs[dataset.id].items():
                    ann = sly.PointcloudAnnotation.from_json(anns[dataset.id][ptc_id], res_project_meta)
                    objects.extend([obj for obj in ann.objects])
                    figures = ann.figures
                    frames.append(sly.Frame(frame_ind, figures))

                objects = PointcloudObjectCollection(objects)
                annotation = sly.PointcloudEpisodeAnnotation(
                    frames_count=len(anns[dataset.id]),
                    objects=objects, 
                    frames=FrameCollection(frames), 
                    tags=VideoTagCollection([]))

            elif state["task"] == "det_and_track":
                tracking_preds = track(raw_results[dataset.id])
                objects, figures = get_objects_and_figures(tracking_preds, res_project_meta)
                objects = PointcloudObjectCollection(objects)
                frames = []
                for ptc_id, figures in figures.items():
                    frames.append(sly.Frame(ptcs_to_frames[dataset.id][ptc_id], figures))
                annotation = sly.PointcloudEpisodeAnnotation(
                    frames_count=len(tracking_preds), 
                    objects=objects, 
                    frames=FrameCollection(frames), 
                    tags=VideoTagCollection([]))

            api.pointcloud_episode.annotation.append(dataset.id,
                                                    annotation,
                                                    frames_to_ptcs[dataset.id],
                                                    KeyIdMap())
            upload_anns_progress.iter_done_report()
            _update_progress(upload_anns_progress, "UploadAnns")
    
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

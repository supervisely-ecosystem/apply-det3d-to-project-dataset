import os
import supervisely as sly
from supervisely.api.module_api import ApiField
from supervisely.video_annotation.key_id_map import KeyIdMap
from supervisely.pointcloud_annotation.constants import OBJECT_KEY
from uuid import UUID

def clone_project(api: sly.Api, workspace_id: int, project_id: int, project_type: str, project_meta: sly.ProjectMeta, new_project_name: str, clone_with_anns: bool):
    if project_type == sly.ProjectType.POINT_CLOUDS.value:
        return clone_pcd_project(api, workspace_id, project_id, project_meta, new_project_name, clone_with_anns)
    elif project_type == sly.ProjectType.POINT_CLOUD_EPISODES.value:
        return clone_pcd_episode_project(api, workspace_id, project_id, project_meta, new_project_name, clone_with_anns)
    else:
        raise ValueError(f"Unsupported project type: {project_type}")

def clone_pcd_project(api: sly.Api, workspace_id:int, project_id: int, project_meta: sly.ProjectMeta, new_project_name: str, clone_with_anns: bool):
    key_id_map_initial = KeyIdMap()
    key_id_map_new = KeyIdMap()

    new_project = api.project.create(
        workspace_id=workspace_id,
        name=new_project_name,
        type=sly.ProjectType.POINT_CLOUDS,
        description="",
        change_name_if_conflict=True,
    )
    api.project.update_meta(new_project.id, project_meta.to_json())

    datasets = api.dataset.get_list(project_id, recursive=True)
    for dataset in datasets:
        dst_dataset = api.dataset.create(
            project_id=new_project.id,
            name=dataset.name,
            description=dataset.description,
            change_name_if_conflict=True,
        )
        pcds_infos = api.pointcloud.get_list(dataset_id=dataset.id)
        progress = sly.Progress(
            message=f"Cloning pointclouds from dataset: {dataset.name}",
            total_cnt=len(pcds_infos),
        )
        for pcd_info in pcds_infos:
            if pcd_info.hash:
                new_pcd_info = api.pointcloud.upload_hash(
                    dataset_id=dst_dataset.id,
                    name=pcd_info.name,
                    hash=pcd_info.hash,
                    meta=pcd_info.meta,
                )

                if clone_with_anns:
                    ann_json = api.pointcloud.annotation.download(pointcloud_id=pcd_info.id)
                    ann = sly.PointcloudAnnotation.from_json(
                        data=ann_json, project_meta=project_meta, key_id_map=key_id_map_initial
                    )

                    api.pointcloud.annotation.append(
                        pointcloud_id=new_pcd_info.id, ann=ann, key_id_map=key_id_map_new
                    )

                rel_images = api.pointcloud.get_list_related_images(id=pcd_info.id)
                if len(rel_images) > 0:
                    rimg_infos = []
                    if clone_with_anns:
                        rimg_figures = {}
                        rimg_ids = [rel_img[ApiField.ID] for rel_img in rel_images]
                        batch_rimg_figures = api.image.figure.download(
                            dataset_id=dataset.id, image_ids=rimg_ids
                        )

                    for rel_img in rel_images:
                        rimg_infos.append(
                            {
                                ApiField.ENTITY_ID: new_pcd_info.id,
                                ApiField.NAME: rel_img[ApiField.NAME],
                                ApiField.HASH: rel_img[ApiField.HASH],
                                ApiField.META: rel_img[ApiField.META],
                            }
                        )

                        if clone_with_anns:
                            rel_image_id = rel_img[ApiField.ID]
                            if rel_image_id in batch_rimg_figures:
                                figs = batch_rimg_figures[rel_image_id]
                                figs_json = []
                                for fig in figs:
                                    fig_json = fig.to_json()
                                    fig_json[OBJECT_KEY] = str(
                                        key_id_map_initial.get_object_key(fig_json[ApiField.OBJECT_ID])
                                    )
                                    fig_json.pop(ApiField.OBJECT_ID, None)
                                    figs_json.append(fig_json)
                                rimg_figures[rel_img[ApiField.HASH]] = figs_json

                    uploaded_rimgs = api.pointcloud.add_related_images(rimg_infos)

                    if not clone_with_anns:
                        # Skip figure processing if annotations cloning is disabled
                        pass
                    
                    else:
                        hash_to_id = {}
                        for info, uploaded in zip(rimg_infos, uploaded_rimgs):
                            img_hash = info.get(ApiField.HASH)
                            img_id = (
                                uploaded.get(ApiField.ID)
                                if isinstance(uploaded, dict)
                                else getattr(uploaded, "id", None)
                            )
                            if img_hash is not None and img_id is not None:
                                hash_to_id[img_hash] = img_id

                        # Prepare figures payload for upload
                        figures_payload = []
                        for img_hash, figs_json in rimg_figures.items():
                            if img_hash not in hash_to_id:
                                continue
                            img_id = hash_to_id[img_hash]
                            for fig in figs_json:
                                try:
                                    fig[ApiField.ENTITY_ID] = img_id
                                    fig[ApiField.DATASET_ID] = dst_dataset.id
                                    fig[ApiField.PROJECT_ID] = project_id
                                    fig[ApiField.OBJECT_ID] = key_id_map_new.get_object_id(
                                        UUID(fig[OBJECT_KEY])
                                    )
                                except Exception:
                                    continue
                            figures_payload.extend(figs_json)

                        # Upload figures in bulk if any
                        if len(figures_payload) > 0:
                            api.image.figure.create_bulk(
                                figures_json=figures_payload, dataset_id=dst_dataset.id
                            )
            else:
                sly.logger.warn(f"{pcd_info.name} have no hash. Item will be skipped.")
                continue

            progress.iter_done_report()

    return new_project

def clone_pcd_episode_project(api: sly.Api, workspace_id:int, project_id: int, project_meta: sly.ProjectMeta, new_project_name: str, clone_with_anns: bool):
    key_id_map_initial = KeyIdMap()
    key_id_map_new = KeyIdMap()
    pcl_to_hash_to_id = {}
    pcl_to_rimg_figures = {}

    new_project = api.project.create(
        workspace_id=workspace_id,
        name=new_project_name,
        type=sly.ProjectType.POINT_CLOUD_EPISODES,
        description="",
        change_name_if_conflict=True,
    )
    datasets = api.dataset.get_list(project_id, recursive=True)

    for dataset in datasets:
        dst_dataset = api.dataset.create(
            project_id=new_project.id,
            name=dataset.name,
            description=dataset.description,
            change_name_if_conflict=True,
        )

        pcd_episodes_infos = api.pointcloud_episode.get_list(dataset_id=dataset.id)
        if clone_with_anns:
            ann_json = api.pointcloud_episode.annotation.download(dataset_id=dataset.id)
            ann = sly.PointcloudEpisodeAnnotation.from_json(
                data=ann_json, project_meta=project_meta, key_id_map=key_id_map_initial
            )
        else:
            ann = None

        frame_to_pointcloud_ids = {}

        progress = sly.Progress(
            message=f"Cloning pointcloud episodes from dataset: {dataset.name}",
            total_cnt=len(pcd_episodes_infos),
        )
        for pcd_episode_info in pcd_episodes_infos:
            if pcd_episode_info.hash:
                new_pcd_episode_info = api.pointcloud_episode.upload_hash(
                    dataset_id=dst_dataset.id,
                    name=pcd_episode_info.name,
                    hash=pcd_episode_info.hash,
                    meta=pcd_episode_info.meta,
                )
                frame_to_pointcloud_ids[new_pcd_episode_info.meta["frame"]] = (
                    new_pcd_episode_info.id
                )
                rel_images = api.pointcloud_episode.get_list_related_images(id=pcd_episode_info.id)
                if len(rel_images) > 0:
                    rimg_infos = []

                    if clone_with_anns:
                        rimg_ids = [rimg[ApiField.ID] for rimg in rel_images]
                        batch_rimg_figures = api.image.figure.download(
                            dataset_id=dataset.id, image_ids=rimg_ids
                        )
                    else:
                        batch_rimg_figures = {}

                    for rel_img in rel_images:
                        rimg_infos.append(
                            {
                                ApiField.ENTITY_ID: new_pcd_episode_info.id,
                                ApiField.NAME: rel_img[ApiField.NAME],
                                ApiField.HASH: rel_img[ApiField.HASH],
                                ApiField.META: rel_img[ApiField.META],
                            }
                        )

                        if clone_with_anns:
                            rel_image_id = rel_img[ApiField.ID]
                            if rel_image_id in batch_rimg_figures:
                                figs = batch_rimg_figures[rel_image_id]
                                figs_json = []
                                for fig in figs:
                                    fig_json = fig.to_json()
                                    fig_json[OBJECT_KEY] = str(
                                        key_id_map_initial.get_object_key(fig_json[ApiField.OBJECT_ID])
                                    )
                                    fig_json.pop(ApiField.OBJECT_ID, None)
                                    figs_json.append(fig_json)

                                pcl_to_rimg_figures.setdefault(new_pcd_episode_info.id, {})[
                                    rel_img[ApiField.HASH]
                                ] = figs_json

                    uploaded_rimgs = api.pointcloud_episode.add_related_images(rimg_infos)
                    if clone_with_anns:
                        for info, uploaded in zip(rimg_infos, uploaded_rimgs):
                            img_hash = info.get(ApiField.HASH)
                            img_id = (
                                uploaded.get(ApiField.ID)
                                if isinstance(uploaded, dict)
                                else getattr(uploaded, "id", None)
                            )
                            if img_hash is not None and img_id is not None:
                                pcl_to_hash_to_id.setdefault(new_pcd_episode_info.id, {})[
                                    img_hash
                                ] = img_id
            else:
                sly.logger.warn(f"{pcd_episode_info.name} have no hash. Item will be skipped.")
                continue

            progress.iter_done_report()

        if clone_with_anns:
            api.pointcloud_episode.annotation.append(
                dataset_id=dst_dataset.id,
                ann=ann,
                frame_to_pointcloud_ids=frame_to_pointcloud_ids,
                key_id_map=key_id_map_new,
            )

            figures_payload = []
            for pcl_id, hash_to_figs in pcl_to_rimg_figures.items():
                hash_map = pcl_to_hash_to_id.get(pcl_id, {})
                for img_hash, figs_json in hash_to_figs.items():
                    if img_hash not in hash_map:
                        continue
                    img_id = hash_map[img_hash]
                    for fig in figs_json:
                        try:
                            fig[ApiField.ENTITY_ID] = img_id
                            fig[ApiField.DATASET_ID] = dst_dataset.id
                            fig[ApiField.PROJECT_ID] = project_id
                            fig[ApiField.OBJECT_ID] = key_id_map_new.get_object_id(
                                UUID(fig[OBJECT_KEY])
                            )
                        except Exception:
                            continue
                    figures_payload.extend(figs_json)

            if len(figures_payload) > 0:
                api.image.figure.create_bulk(figures_json=figures_payload, dataset_id=dst_dataset.id)

    return new_project
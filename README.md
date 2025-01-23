<div align="center" markdown>

<img src="https://user-images.githubusercontent.com/48245050/182627503-8dab4d23-8c6d-43fc-aea7-14abb4a14d03.png"/>

# Apply 3D Detection to Pointcloud Project

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Usage">Usage</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Result">Result</a> •
  <a href="#Related-Apps">Related Apps</a> •
  <a href="#Related-Projects">Related Projects</a> •
  <a href="#Screenshot">Screenshot</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/apply-det3d-to-project-dataset)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/apply-det3d-to-project-dataset)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/apply-det3d-to-project-dataset.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/apply-det3d-to-project-dataset.png)](https://supervisely.com)

</div>

# Overview

This app provides convenient inference interface for 3d neural networks on pointclouds. Just connect to your deployed model, select model classes and model predictions will be saved to a new project. 

Application key points:

- Works with both separate pointclouds and pointcloud episodes
- Support 3d tracking

# Usage

<a data-key="sly-embeded-video-link" href="https://youtu.be/QThlasFmEUA" data-video-code="QThlasFmEUA">
    <img src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/youtube-image.png" alt="SLY_EMBEDED_VIDEO_LINK"  style="max-width:50%;">
</a>



# How To Run
**Step 0.** Please make sure that you deployed 3d detection model using corresponding serving app. Learn more in ecosystem …

**Step 1.** Add [Apply 3D Detection to Pointcloud Project](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/apply-det3d-to-project-dataset) application to your Team

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/apply-det-and-cls-models-to-project" src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/thumb.png" width="550px"/>

**Step 2.** Launch from Pointcloud Project's context menu

<img src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/runapp.png" style="width: 100%;"/>

**Step 3.** Press the Run button in the modal window

<img src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/modal.png" style="width: 70%;"/>

# Result

<img src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/result.png" style="width: 100%;"/>

# Related Apps

1. [Train MMDetection3D](https://app.supervisely.com/ecosystem/apps/mmdetection_3d/train) - start training on your custom data. Just run app from the context menu of your project, choose classes of interest, train/val splits, configure training parameters and augmentations, and monitor training metrics in realtime. All training artifacts including model weights will be saved to Team Files and can be easily downloaded. 

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/mmdetection_3d/train" src="https://user-images.githubusercontent.com/97401023/192003567-4446f620-6540-4e68-a6a1-d3a9fcc85fbc.png" width="350px"/>

2. [Serve MMDetection3D](https://app.supervisely.com/ecosystem/apps/mmdetection_3d/serve) - serve model as Rest API service. You can run pretrained model, use custom model weights trained in Supervisely. Thus other apps from Ecosystem can get predictions from the deployed model. Also developers can send inference requiests in a few lines of python code.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/mmdetection_3d/serve" src="https://user-images.githubusercontent.com/97401023/192003614-4dbe1828-e9c1-4c78-bf89-8f3115103d29.png" width="350px"/>

3. [Import KITTI 3D](https://app.supervisely.com/ecosystem/apps/import-kitti-3d) - app allows to get sample from KITTI 3D dataset or upload your downloaded KITTI data to Supervisely in point clouds project format.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/import-kitti-3d" src="https://user-images.githubusercontent.com/97401023/192003697-a6aa11c4-df2e-46cc-9072-b9937756c51b.png" width="350px"/>

4. [Import KITTI-360](https://app.supervisely.com/ecosystem/apps/import-kitti-360/supervisely_app) - app allows to upload your downloaded KITTI-360 data to Supervisely in point cloud episodes project format.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/import-kitti-360/supervisely_app" src="https://user-images.githubusercontent.com/97401023/192003741-0fd62655-60c3-4e57-80e8-85f936fc0f8d.png" width="350px"/>

# Related Projects

1. [Demo LYFT 3D dataset annotated](https://app.supervisely.com/ecosystem/projects/demo-lyft-3d-dataset-annotated) - demo sample from [Lyft](https://level-5.global/data) dataset with labels.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/demo-lyft-3d-dataset-annotated" src="https://user-images.githubusercontent.com/97401023/192003812-1cefef97-29e3-40dd-82c6-7d3cf3d55585.png" width="400px"/>

2. [Demo LYFT 3D dataset](https://app.supervisely.com/ecosystem/projects/demo-lyft-3d-dataset) - demo sample from [Lyft](https://level-5.global/data) dataset without labels.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/demo-lyft-3d-dataset" src="https://user-images.githubusercontent.com/97401023/192003862-102de613-d365-4043-8ca0-d59e3c95659a.png" width="400px"/>

3. [Demo KITTI pointcloud episodes annotated](https://app.supervisely.com/ecosystem/projects/demo-kitti-3d-episodes-annotated) - demo sample from [KITTI 3D](https://www.cvlibs.net/datasets/kitti/eval_tracking.php) dataset with labels.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/demo-kitti-3d-episodes-annotated" src="https://user-images.githubusercontent.com/97401023/192003917-71425add-e985-4a9c-8739-df832324be2f.png" width="400px"/>

4. [Demo KITTI pointcloud episodes](https://app.supervisely.com/ecosystem/projects/demo-kitti-3d-episodes) - demo sample from [KITTI 3D](https://www.cvlibs.net/datasets/kitti/eval_tracking.php) dataset without labels.

    <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/demo-kitti-3d-episodes" src="https://user-images.githubusercontent.com/97401023/192003975-972c1803-b502-4389-ae83-72958ddd89ad.png" width="400px"/>

   

# Screenshot

<img src="https://github.com/supervisely-ecosystem/apply-det3d-to-project-dataset/releases/download/v0.0.1/app_ui_screenshot.png" style="width: 100%;"/>

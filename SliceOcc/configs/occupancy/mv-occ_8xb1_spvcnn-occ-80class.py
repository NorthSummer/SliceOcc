_base_ = ['../default_runtime.py']
n_points = 100000

# origin for multi-view scannet is set to 0.5
# -1.28~1.28 -> -0.78~1.78
point_cloud_range = [-3.2, -3.2, -0.78, 3.2, 3.2, 1.78]
cam_point_range = [-3.2, -3.2, -1.28, 3.2, 3.2, 1.28]



prior_generator = dict(type='AlignedAnchor3DRangeGenerator',
                       ranges=[[-3.2, -3.2, -1.28, 3.2, 3.2, 1.28]],
                       rotations=[.0])


_dim_ = 256
_pos_dim_ = _dim_//2
_ffn_dim_ = _dim_*2
_num_levels_ = 4
_num_cams_ = 20
tpv_h_ = 40
tpv_w_ = 40
tpv_z_ = 16
anchor_z_ = 16
num_slices_ = 8
scale_h = 1
scale_w = 1
scale_z = 1
num_points_in_pillar = [3] * 2 * num_slices_ #这里也可以做消融实验，对显存影响较大
num_points = [6] * 2 * num_slices_
nbr_class = 81



model = dict(
    type='DenseFusionOccPredictor',
    use_valid_mask=False,
    use_xyz_feat=True,
    point_cloud_range=point_cloud_range,
    data_preprocessor=dict(type='Det3DDataPreprocessor',
                           mean=[123.675, 116.28, 103.53],
                           std=[58.395, 57.12, 57.375],
                           bgr_to_rgb=True,
                           pad_size_divisor=32),
    backbone=dict(type='mmdet.ResNet',
                  depth=50,
                  num_stages=4,
                  out_indices=(0, 1, 2, 3),
                  frozen_stages=1,
                  norm_cfg=dict(type='BN', requires_grad=False),
                  norm_eval=True,
                  init_cfg=dict(type='Pretrained',
                                checkpoint='torchvision://resnet50'),
                  style='pytorch'),
    neck=dict(type='mmdet.FPN',
              in_channels=[256, 512, 1024, 2048],
              out_channels=256,
              num_outs=4),
    #backbone_3d=dict(type='MinkResNet', in_channels=3, depth=34),
    #backbone_3d=dict(type='cylinder_asym'),
    backbone_3d=dict(type='SPVCNN',
                     num_classes=81,
                     pres=0.16,
                     vres=0.16,
                     cr=1.0),
    neck_3d=dict(type='IndoorImVoxelNeck',
                 in_channels=256,
                 out_channels=128,
                 n_blocks=[1, 1, 1]),
    bbox_head=dict(
        type='ImVoxelOccHead',
        volume_h=[20, 10, 5],
        volume_w=[20, 10, 5],
        volume_z=[8, 4, 2],
        num_classes=81,  # TO Be changed
        in_channels=[128, 128, 128], #[128, 128, 128],
        use_semantic=True),
    prior_generator=prior_generator,
    n_voxels=[40, 40, 16],  
    n_anchors=[40, 40, 16],
    coord_type='DEPTH',
)

dataset_type = 'EmbodiedScanDataset'
data_root = 'data'
class_names = ('floor', 'wall', 'chair', 'cabinet', 'door', 'table', 'couch',
               'shelf', 'window', 'bed', 'curtain', 'desk', 'doorframe',
               'plant', 'stairs', 'pillow', 'wardrobe', 'picture', 'bathtub',
               'box', 'counter', 'bench', 'stand', 'rail', 'sink', 'clothes',
               'mirror', 'toilet', 'refrigerator', 'lamp', 'book', 'dresser',
               'stool', 'fireplace', 'tv', 'blanket', 'commode',
               'washing machine', 'monitor', 'window frame', 'radiator', 'mat',
               'shower', 'rack', 'towel', 'ottoman', 'column', 'blinds',
               'stove', 'bar', 'pillar', 'bin', 'heater', 'clothes dryer',
               'backpack', 'blackboard', 'decoration', 'roof', 'bag', 'steps',
               'windowsill', 'cushion', 'carpet', 'copier', 'board',
               'countertop', 'basket', 'mailbox', 'kitchen island',
               'washbasin', 'bicycle', 'drawer', 'oven', 'piano',
               'excercise equipment', 'beam', 'partition', 'printer',
               'microwave', 'frame')

metainfo = dict(classes=class_names,
                occ_classes=class_names,
                box_type_3d='euler-depth')
backend_args = None

train_pipeline = [
    dict(type='LoadAnnotations3D',
         with_occupancy=True,
         with_visible_occupancy_masks=True),
    dict(type='MultiViewPipeline',
         n_images=20,
         transforms=[
             dict(type='LoadImageFromFile', backend_args=backend_args),
             dict(type='LoadDepthFromFile', backend_args=backend_args),
             dict(type='ConvertRGBDToPoints', coord_type='CAMERA'),
             dict(type='PointSample', num_points=n_points // 10),
             dict(type='Resize', scale=(480, 480), keep_ratio=False)
         ]),
    dict(type='AggregateMultiViewPoints', coord_type='DEPTH'),
    dict(type='PointsRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='PointSample', num_points=n_points),
    dict(type='ConstructMultiViewMasks'),
    dict(
        type='Pack3DDetInputs',
        keys=['img', 'points', 'gt_bboxes_3d', 'gt_labels_3d', 'gt_occupancy'])
]

test_pipeline = [
    dict(type='LoadAnnotations3D',
         with_occupancy=True,
         with_visible_occupancy_masks=True),
    dict(type='MultiViewPipeline',
         n_images=20,
         ordered=True,
         transforms=[
             dict(type='LoadImageFromFile', backend_args=backend_args),
             dict(type='LoadDepthFromFile', backend_args=backend_args),
             dict(type='ConvertRGBDToPoints', coord_type='CAMERA'),
             dict(type='PointSample', num_points=n_points // 10),
             dict(type='Resize', scale=(480, 480), keep_ratio=False)
         ]),
    dict(type='AggregateMultiViewPoints', coord_type='DEPTH'),
    dict(type='PointsRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='PointSample', num_points=n_points),
    dict(type='ConstructMultiViewMasks'),
    dict(
        type='Pack3DDetInputs',
        keys=['img', 'points', 'gt_bboxes_3d', 'gt_labels_3d', 'gt_occupancy'])
]

train_dataloader = dict(batch_size=1,
                        num_workers=1,
                        persistent_workers=True,
                        sampler=dict(type='DefaultSampler', shuffle=True),
                        dataset=dict(type=dataset_type,
                                     data_root=data_root,
                                     ann_file='embodiedscan_infos_train.pkl',
                                     pipeline=train_pipeline,
                                     test_mode=False,
                                     filter_empty_gt=True,
                                     box_type_3d='Euler-Depth',
                                     metainfo=metainfo))

val_dataloader = dict(batch_size=1,
                      num_workers=1,
                      persistent_workers=True,
                      drop_last=False,
                      sampler=dict(type='DefaultSampler', shuffle=False),
                      dataset=dict(type=dataset_type,
                                   data_root=data_root,
                                   ann_file='embodiedscan_infos_val.pkl',
                                   pipeline=test_pipeline,
                                   test_mode=True,
                                   filter_empty_gt=True,
                                   box_type_3d='Euler-Depth',
                                   metainfo=metainfo))
test_dataloader = val_dataloader

val_evaluator = dict(type='OccupancyMetric')
test_evaluator = val_evaluator

train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=24, val_interval=4) #32
val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')

# optimizer
optim_wrapper = dict(type='OptimWrapper',
                     optimizer=dict(type='AdamW', lr=1e-4, weight_decay=0.01),
                     clip_grad=dict(max_norm=35., norm_type=2))
param_scheduler = dict(type='MultiStepLR',
                       begin=0,
                       end=24,
                       by_epoch=True,
                       milestones=[16, 20],
                       gamma=0.1)

custom_hooks = [dict(type='EmptyCacheHook', after_iter=True)]

# hooks
default_hooks = dict(
    checkpoint=dict(type='CheckpointHook', interval=24, max_keep_ckpts=24))

# runtime
find_unused_parameters = True  # only 1 of 4 FPN outputs is used
visualizer = dict(type='EmbodiedScanBaseVisualizer', vis_backends=[dict(type='LocalVisBackend')], save_dir='temp_dir')
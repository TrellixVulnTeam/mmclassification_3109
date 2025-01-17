# dataset settings
dataset_type = 'VOC'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='RandomResizedCrop', size=224),
    dict(type='RandomFlip', flip_prob=0.5, direction='horizontal'),
    dict(
        type='Normalize',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        to_rgb=True),
    dict(type='ImageToTensor', keys=['img']),
    dict(type='ToTensor', keys=['gt_label']),
    dict(type='Collect', keys=['img', 'gt_label'])
]
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', size=(256, -1)),
    dict(type='CenterCrop', crop_size=224),
    dict(
        type='Normalize',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        to_rgb=True),
    dict(type='ImageToTensor', keys=['img']),
    dict(type='Collect', keys=['img'])
]
data = dict(
    samples_per_gpu=16,
    workers_per_gpu=2,
    train=dict(
        type=dataset_type,
        data_prefix='data/VOCdevkit/VOC2007/',
        ann_file='data/VOCdevkit/VOC2007/ImageSets/Main/trainval.txt',
        pipeline=train_pipeline),
    val=dict(
        type=dataset_type,
        data_prefix='data/VOCdevkit/VOC2007/',
        ann_file='data/VOCdevkit/VOC2007/ImageSets/Main/test.txt',
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        data_prefix='data/VOCdevkit/VOC2007/',
        ann_file='data/VOCdevkit/VOC2007/ImageSets/Main/test.txt',
        pipeline=test_pipeline))
evaluation = dict(
    interval=1, 
    metric=['mAP', 'CP', 'OP', 'CR', 'OR', 'CF1', 'OF1'],
    save_best='mAP',
)

# training settings
log_config = dict(interval=20, hooks=[dict(type='TextLoggerHook')])
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = '/home/jack/Projects/openmmlab/mmclassification/work_dirs/train/jz_t40_resnet_multi_lable_8bit/best_mAP_epoch_280.pth'
resume_from = None
workflow = [('train', 1)]

# checkpoint saving
checkpoint_config = dict(interval=1,)

# junzhen settings
'''
注意：
- 最新的Maigk-OPs插件bool值类型不支持传入0-1，需强制指定True或False；
- 8bit和32bit训练参数可保持一致，4bit学习率建议调小10倍；【参考如下】
    - 32bit：SGD+LR(0.1)
    - 8 bit：SGD+LR(0.1)
    - 4 bit: Adam+LR(0.01)
- 如调参后发现4bit精度很差或者收敛曲线震荡还是很厉害，请使用4-8bit混合精度量化。
'''
num_classes = 20
optimizer_type = "SGD"

is_quantize = True
bitw = 4
if bitw==8:
    bita = 8
    weight_factor = 3.0
    clip_max_value = 6.0
    optimizer_lr = 0.1
    optimizer_type = optimizer_type
elif bitw==4:
    bita = 4
    weight_factor = 3.0
    clip_max_value = 4.0
    optimizer_lr = 0.01
    optimizer_type = optimizer_type
elif bitw==2:
    bita = 2
    weight_factor = 2.0
    clip_max_value = 2.0
    optimizer_lr = 0.01
    optimizer_type = optimizer_type
else:
    bita = 32
    weight_factor = 3.
    clip_max_value = 6.
    optimizer_lr = 0.1
    optimizer_type = optimizer_type
target_device = "T40"

# model settings
model = dict(
    type='ImageClassifier',
    backbone=dict(
        type='T40ResNet',
        depth=18,
        is_quantize=is_quantize,
        bita=bita,
        bitw=bitw,
        clip_max_value=clip_max_value,
        weight_factor=weight_factor,
        target_device=target_device,
    ),
    neck=dict(
        type='T40GlobalAveragePooling',
        in_channels=512,
        is_quantize=is_quantize,
        bita=bita,
        target_device=target_device,
    ),
    head=dict(
        type='T40MultiLabelLinearClsHead',
        num_classes=num_classes,
        in_channels=512,
        loss=dict(
            type='CrossEntropyLoss', 
            use_sigmoid=True, 
            loss_weight=1.0,
            reduction='mean'
        ),
        is_quantize=is_quantize, 
        bita=bita, 
        bitw=bitw,
        clip_max_value=clip_max_value, 
        weight_factor=weight_factor,
        target_device=target_device,
    )
)

# ---------- Schedules Setting ---------- #
# optimizer
optimizer = dict(type=optimizer_type, lr=optimizer_lr, momentum=0.9, weight_decay=5e-4)
optimizer_config = dict(grad_clip=None)

# learning policy
lr_config = dict(policy='step', step=[90, 180, 270])
runner = dict(type='EpochBasedRunner', max_epochs=1)
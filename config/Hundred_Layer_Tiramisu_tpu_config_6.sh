# Hundred Layer Tiramisu tpu training configuration: 
# Run date: 15.06.2020 (during the day)

# 1. 
python3 main.py --batch_size=8 --base_learning_rate=1.0e-03 --lr_warmup_epochs=1 --lr_drop_ratio=0.8 --train_epochs=40 --model_architecture=100-Layer-Tiramisu --tfrec_dir=gs://oai-challenge-dataset/tfrecords/ --logdir=gs://oai-challenge-dataset/checkpoints/ --tpu=lapo-tpu



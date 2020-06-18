import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import ArtistAnimation
import os.path

import glob
from google.cloud import storage
from pathlib import Path
import os
from datetime import datetime

from Segmentation.utils.losses import dice_coef
from Segmentation.plotting.voxels import plot_volume
from Segmentation.utils.training_utils import visualise_binary, visualise_multi_class
from Segmentation.utils.evaluation_metrics import get_confusion_matrix, plot_confusion_matrix

def get_depth(conc):
    depth = 0
    for batch in conc:
        depth += batch.shape[0]
    return depth

def plot_and_eval_3D(trained_model,
                     logdir,
                     visual_file,
                     tpu_name,
                     bucket_name,
                     weights_dir,
                     is_multi_class,
                     save_freq,
                     dataset):

    # load the checkpoints in the specified log directory
    train_hist_dir = os.path.join(logdir, tpu_name)
    train_hist_dir = os.path.join(train_hist_dir, visual_file)
    checkpoints = Path(train_hist_dir).glob('*')

    ######################
    """ Add the visualisation code here """
    print("Training history directory: {}".format(train_hist_dir))
    print("+========================================================")
    print(f"Does the selected path exist: {Path(train_hist_dir).is_dir()}")
    print(f"The glob object is: {checkpoints}")
    print("\n\nThe directories are:")
    print('weights_dir == "checkpoint"',weights_dir == "checkpoint")
    print('weights_dir',weights_dir)
    ######################

    session_name = os.path.join(weights_dir, tpu_name, visual_file)

    # Get names within folder in gcloud
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name)
    session_content = []
    tf_records_content = []
    for blob in blobs:
        if session_name in blob.name:
            session_content.append(blob.name)
        if os.path.join('tfrecords', 'valid') in blob.name:
            tf_records_content.append(blob.name)

    session_weights = []
    for item in session_content:
        if ('_weights' in item) and ('.ckpt.index' in item):
            session_weights.append(item)

    ######################
    for s in session_weights:
        print(s)
    print("--")
    ######################

    # Only use part of dataset
    idx_vol= 0 # how many numpies have been save
    target = 160
    
    for i, chkpt in enumerate(session_weights):
        should_save_np = np.mod(i, save_freq) == 0
        
        ######################
        print('should_save_np',should_save_np)
        print('checkpoint enum i',i)
        print('save_freq set to ',save_freq)
        ######################

        if not should_save_np:      # skip this checkpoint weight
            print("skipping ", chkpt)
            continue

        name = chkpt.split('/')[-1]
        name = name.split('.inde')[0]
        trained_model.load_weights('gs://' + os.path.join(bucket_name,
                                                          weights_dir,
                                                          tpu_name,
                                                          visual_file,
                                                          name)).expect_partial()


        # sample_x = []    # x for current 160,288,288 vol
        sample_pred = []  # prediction for current 160,288,288 vol
        sample_y = []    # y for current 160,288,288 vol


        for idx, ds in enumerate(dataset):

            ######################
            print(f"the index is {idx}")
            print('Current chkpt name',name)
            ######################

            x, y = ds
            batch_size = x.shape[0]
            x = np.array(x)
            y = np.array(y)
        
            pred = trained_model.predict(x)

            ######################
            print("Current batch size set to {}. Target depth is {}".format(batch_size, target))
            print('Input image data type: {}, shape: {}'.format(type(x), x.shape))
            print('Ground truth data type: {}, shape: {}'.format(type(y), y.shape))
            print('Prediction data type: {}, shape: {}'.format(type(pred), pred.shape))
            print("=================")
            ######################

            if (get_depth(sample_pred) + batch_size) < target:  # check if next batch will fit in volume (160)
                sample_pred.append(pred)
                del pred
                sample_y.append(y)
                del y
            else:
                remaining = target - get_depth(sample_pred)
                sample_pred.append(pred[:remaining])
                sample_y.append(y[:remaining])
                pred_vol = np.concatenate(sample_pred)
                del sample_pred
                y_vol = np.concatenate(sample_y)
                del sample_y
                sample_pred = [pred[remaining:]]
                sample_y = [y[remaining:]]

                del pred
                del y

                ######################
                print("===============")
                print("pred done")
                print(pred_vol.shape)
                print(y_vol.shape)
                print("===============")
                print('is_multi_class', is_multi_class)
                ######################

                if is_multi_class:  # or np.shape(pred_vol)[-1] not
                    pred_vol = np.argmax(pred_vol, axis=-1)
                    y_vol = np.argmax(y_vol, axis=-1)

                    ######################
                    print('np.shape(pred_vol)', np.shape(pred_vol))
                    print('np.shape(y_vol)',np.shape(y_vol))
                    ######################

                # Save volume as numpy file for plotlyyy
                fig_dir = "results"
                name_pred_npy = os.path.join(fig_dir, "pred", (visual_file + "_" + name + "_" +str(idx_vol).zfill(3)))
                name_y_npy = os.path.join(fig_dir, "ground_truth", (visual_file + "_" + name + "_" + str(idx_vol).zfill(3)))
                
                ######################
                print("npy save pred as ", name_pred_npy)
                print("npy save y as ", name_y_npy)
                print("Currently on vol ", idx_vol)
                ######################


                # Get middle xx slices cuz 288x288x160 too big
                roi = int(50 / 2)
                d1,d2,d3 = np.shape(pred_vol)[0:3]
                d1, d2, d3 = int(np.floor(d1/2)), int(np.floor(d2/2)), int(np.floor(d3/2))
                pred_vol = pred_vol[(d1-roi):(d1+roi),(d2-roi):(d2+roi), (d3-roi):(d3+roi)]
                d1,d2,d3 = np.shape(y_vol)[0:3]
                d1, d2, d3 = int(np.floor(d1/2)), int(np.floor(d2/2)), int(np.floor(d3/2))
                y_vol = y_vol[(d1-roi):(d1+roi),(d2-roi):(d2+roi), (d3-roi):(d3+roi)]

                ######################
                print('y_vol.shape', np.shape(y_vol))
                ######################

                np.save(name_pred_npy,pred_vol)
                np.save(name_y_npy,y_vol)
                idx_vol += 1
                del pred_vol
                del y_vol

                ######################
                print("breaking after saving vol ", idx, "for ", name)
                ######################
                break


                

            print("=================")


            

def pred_evolution_gif(frames_list,
                       interval=200,
                       save_dir='',
                       file_name=''):

    fig = plt.Figure()
    gif = ArtistAnimation(fig, frames_list, interval) # create gif

    # save file
    # save_dir = save_dir.replace("/", "\\\\")
    # save_dir = save_dir.replace("\\", "\\\\")

    plt.rcParams['animation.ffmpeg_path'] = r'//opt//conda//bin//ffmpeg'  # change directory for animations
    save_dir = save_dir + '/' + file_name
    print(save_dir)

    if not save_dir == '':
        if file_name == '':
            time = datetime.now().strftime("%Y%m%d-%H%M%S")
            file_name = 'gif'+ time + '.gif'

        
        #gif.save(file_name, writer='ffmpeg')
        #writergif = animation.PillowWriter(fps=30)
        Writer = animation.writers['ffmpeg']
        ffmwriter = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
        #ffmwriter = animation.FFMpegWriter()
        gif.save(save_dir, writer=ffmwriter)
        plt.close('all')
    else:
        plt.show()

def confusion_matrix(trained_model,
                     weights_dir,
                     fig_dir,
                     dataset,
                     validation_steps,
                     multi_class,
                     model_architecture,
                     num_classes=7):

    trained_model.load_weights(weights_dir).expect_partial()
    trained_model.evaluate(dataset, steps=validation_steps)

    if multi_class:
        cm = np.zeros((num_classes, num_classes))
        classes = ["Background",
                   "Femoral",
                   "Medial Tibial",
                   "Lateral Tibial",
                   "Patellar",
                   "Lateral Meniscus",
                   "Medial Meniscus"]
    else:
        cm = np.zeros((2, 2))
        classes = ["Background",
                   "Cartilage"]

    for step, (image, label) in enumerate(dataset):
        print(step)
        pred = trained_model.predict(image)
        cm = cm + get_confusion_matrix(label, pred, classes=list(range(0, num_classes)))

        if step > validation_steps - 1:
            break

    fig_file = model_architecture + '_matrix.png'
    fig_dir = os.path.join(fig_dir, fig_file)
    plot_confusion_matrix(cm, fig_dir, classes=classes)

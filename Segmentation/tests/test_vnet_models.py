import tensorflow as tf

class TestVNet(tf.test.TestCase):

    def test_tiny_vnet(self, n_volumes=3,
                       width=28, height=28, depth=16, colour_channels=1,
                       n_reps=5, n_classes=3, epochs=5):

        from Segmentation.data_gen.toy_volume_gen import get_test_volumes

        volumes, one_hots = get_test_volumes(n_volumes, n_reps, n_classes,
                                             width, height, depth, colour_channels)

        from Segmentation.model.tiny_vnet import VNet_Tiny as VNet
        vnet = VNet(colour_channels, n_classes, merge_connections=True)

        from tensorflow.keras.optimizers import Adam
        from Segmentation.utils.training_utils import tversky_loss, dice_loss
        vnet.compile(optimizer=Adam(0.00001),
                     loss=dice_loss,
                     metrics=['categorical_crossentropy'],
                     experimental_run_tf_function=False)

        # output = vnet(volumes)
        # print("expect:", one_hots.shape)

        history = vnet.fit(volumes, one_hots, epochs=epochs)
        loss_history = history.history['loss']
        loss_history = history.history['loss']
        # self.assertAllGreaterEqual(loss_history, 0.)
        # self.assertGreater(loss_history[0], loss_history[-1])
        pred = vnet.predict(volumes)
        assert pred.shape == one_hots.shape

    def test_small_vnet(self, n_volumes=3,
                        width=32, height=32, depth=32, colour_channels=3,
                        n_reps=5, n_classes=3, epochs=2):

        from Segmentation.data_gen.toy_volume_gen import get_test_volumes

        volumes, one_hots = get_test_volumes(n_volumes, n_reps, n_classes,
                                             width, height, depth, colour_channels)

        from Segmentation.model.small_vnet import VNet_Small as VNet
        vnet = VNet(colour_channels, n_classes, merge_connections=True)

        from tensorflow.keras.optimizers import Adam
        from Segmentation.utils.training_utils import dice_loss
        vnet.compile(optimizer=Adam(0.00001),
                     loss=dice_loss,
                     metrics=['categorical_crossentropy'])
                     # experimental_run_tf_function=False)
        history = vnet.fit(volumes, one_hots, epochs=epochs)
        loss_history = history.history['loss']
        loss_history = history.history['loss']
        pred = vnet.predict(volumes)
        assert pred.shape == one_hots.shape


if __name__ == '__main__':
    import sys
    from os import getcwd
    sys.path.insert(0, getcwd())

    tf.test.main()

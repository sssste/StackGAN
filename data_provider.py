import tensorflow as tf

import configuration

conf = configuration.config()


def parse_data(example):
    features = {
        "image": tf.FixedLenFeature(shape=[], dtype=tf.string),
        "image_shape": tf.FixedLenFeature(shape=[3], dtype=tf.int64),
        "caption": tf.VarLenFeature(tf.float32),
        "caption_shape": tf.FixedLenFeature(shape=[2], dtype=tf.int64)
    }
    par_exm = tf.parse_single_example(example, features=features)
    height = tf.cast(par_exm["image_shape"][1], tf.int32)
    weight = tf.cast(par_exm["image_shape"][0], tf.int32)
    shape = tf.stack([height, weight, 3])
    image = tf.reshape(tf.decode_raw(par_exm["image"], tf.uint8), shape)
    caption = tf.reshape(par_exm["caption"].values, par_exm["caption_shape"])
    return image, caption


def map_Stage_I(example):
    image, caption = parse_data(example)
    resized_image = tf.image.resize_images(image, [conf.small_image_size, conf.small_image_size])
    resized_image = tf.cast(resized_image, tf.float32)
    resized_image = (resized_image - 127.5) / 127.5
    # 随机采样一个其中的caption用于训练
    random = tf.random_uniform([1], 0, tf.shape(caption)[0], dtype=tf.int32)
    single_caption = tf.gather_nd(caption, random)
    return resized_image, single_caption

def map_Stage_II(example):
    image, caption = parse_data(example)
    resized_image = tf.image.resize_images(image, [conf.large_image_size, conf.large_image_size])
    resized_image = tf.cast(resized_image, tf.float32)
    resized_image = (resized_image - 127.5) / 127.5
    # 随机采样一个其中的caption用于训练
    random = tf.random_uniform([1], 0, tf.shape(caption)[0], dtype=tf.int32)
    single_caption = tf.gather_nd(caption, random)
    return resized_image, single_caption



def get_stage_I_train_input_fn():
    data_path = "train.tfrecord"

    def train_input_fn():
        with tf.device("/cpu:0"):
            dataset = tf.data.TFRecordDataset(data_path)
            dataset = dataset.map(map_Stage_I)
            dataset = dataset.shuffle(buffer_size=512)
            dataset = dataset.repeat(conf.epoch)
            dataset = dataset.batch(conf.batch_size)
            iterator = dataset.make_one_shot_iterator()
            image, caption = iterator.get_next()
            caption.set_shape([conf.batch_size, 1024])
            image.set_shape([conf.batch_size, conf.small_image_size, conf.small_image_size, 3])
            noise = tf.random_normal([conf.batch_size, conf.noise_dim])
            return {"noise": noise, "caption": caption}, image

    return train_input_fn

def get_stage_II_train_input_fn():
    data_path = "train.tfrecord"

    def train_input_fn():
        with tf.device("/cpu:0"):
            dataset = tf.data.TFRecordDataset(data_path)
            dataset = dataset.map(map_Stage_II)
            dataset = dataset.shuffle(buffer_size=512)
            dataset = dataset.repeat(conf.epoch)
            dataset = dataset.batch(conf.batch_size)
            iterator = dataset.make_one_shot_iterator()
            image, caption = iterator.get_next()
            caption.set_shape([conf.batch_size, 1024])
            image.set_shape([conf.batch_size, conf.large_image_size, conf.large_image_size, 3])
            noise = tf.random_normal([conf.batch_size, conf.noise_dim])
            return {"noise": noise, "caption": caption}, image

    return train_input_fn


def get_stage_I_predict_input_fn():
    data_path = "test.tfrecord"

    def predict_input_fn():
        with tf.device("/cpu:0"):
            dataset = tf.data.TFRecordDataset(data_path)
            dataset = dataset.map(map_Stage_I)
            dataset = dataset.batch(conf.predict_batch_size)
            iterator = dataset.make_one_shot_iterator()
            _, caption = iterator.get_next()
            caption.set_shape([conf.predict_batch_size, 1024])
            noise = tf.random_normal([conf.predict_batch_size, conf.noise_dim])
            return {"noise": noise, "caption": caption}, _

    return predict_input_fn

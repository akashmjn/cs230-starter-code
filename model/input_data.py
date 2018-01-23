"""Create the input data pipeline using `tf.data`"""

import tensorflow as tf


def _parse_function(filename, label):
    """Obtain the image from the filename (for both training and validation).

    The following operations are applied:
        - Decode the image from jpeg format
        - Convert to float and to range [0, 1]
        - Resize the image to size (224, 224)
    """
    image_string = tf.read_file(filename)

    # Don't use tf.image.decode_image, or the output shape will be undefined
    image_decoded = tf.image.decode_jpeg(image_string, channels=3)

    # This will convert to float values in [0, 1]
    image = tf.image.convert_image_dtype(image_decoded, tf.float32)

    resized_image = tf.image.resize_images(image, [224, 224])
    return resized_image, label


def train_preprocess(image, label):
    """Image preprocessing for training.

    Apply the following operations:
        - Horizontally flip the image with probability 1/2
        - Apply random brightness and saturation
    """
    image = tf.image.random_flip_left_right(image)

    image = tf.image.random_brightness(image, max_delta=32.0 / 255.0)
    image = tf.image.random_saturation(image, lower=0.5, upper=1.5)

    # Make sure the image is still in [0, 1]
    image = tf.clip_by_value(image, 0.0, 1.0)

    return image, label


def input_fn(filenames, params):
    """Input function for the SIGNS dataset.

    The filenames have format "{label}_IMG_{id}.jpg".
    For instance: "data_dir/2_IMG_4584.jpg".

    Args:
        filenames: (list) filenames of the images, as ["data_dir/{label}_IMG_{id}.jpg"...]
        params: (Params) contains hyperparameters of the model (ex: `params.num_epochs`)
    """
    num_samples = len(filenames)
    # Labels will be between 0 and 5 included (6 classes in total)
    labels = [int(filename.split('/')[-1][0]) for filename in filenames]

    # Create a Dataset serving batches of images and labels
    dataset = (tf.data.Dataset.from_tensor_slices((tf.constant(filenames), tf.constant(labels)))
        .shuffle(num_samples)  # whole dataset into the buffer ensures good shuffling
        .repeat(params.num_epochs)
        .map(_parse_function, num_parallel_calls=params.num_parallel_calls)
        .map(train_preprocess, num_parallel_calls=params.num_parallel_calls)
        .batch(params.batch_size)
        .prefetch(1)  # make sure you always have one batch ready to serve
    )

    # Create one shot iterator from dataset
    iterator = dataset.make_one_shot_iterator()
    images, labels = iterator.get_next()

    inputs = {'images': images, 'labels': labels}
    return inputs

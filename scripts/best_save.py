import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import logging

def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

def conv2d(x, W, stride):
    return tf.nn.conv2d(x, W, strides=[1, stride, stride, 1], padding='SAME')

def create_model(x, keep_prob):
    logging.info(f"Input shape: {x.shape}")
    
    #first convolutional layer
    W_conv1 = weight_variable([5, 5, 3, 24])
    b_conv1 = bias_variable([24])
    h_conv1 = tf.nn.relu(conv2d(x, W_conv1, 2) + b_conv1)
    logging.info(f"Conv1 shape: {h_conv1.shape}")

    #second convolutional layer
    W_conv2 = weight_variable([5, 5, 24, 36])
    b_conv2 = bias_variable([36])
    h_conv2 = tf.nn.relu(conv2d(h_conv1, W_conv2, 2) + b_conv2)
    logging.info(f"Conv2 shape: {h_conv2.shape}")

    #third convolutional layer
    W_conv3 = weight_variable([5, 5, 36, 48])
    b_conv3 = bias_variable([48])
    h_conv3 = tf.nn.relu(conv2d(h_conv2, W_conv3, 2) + b_conv3)
    logging.info(f"Conv3 shape: {h_conv3.shape}")

    #fourth convolutional layer
    W_conv4 = weight_variable([3, 3, 48, 64])
    b_conv4 = bias_variable([64])
    h_conv4 = tf.nn.relu(conv2d(h_conv3, W_conv4, 1) + b_conv4)
    logging.info(f"Conv4 shape: {h_conv4.shape}")

    #fifth convolutional layer
    W_conv5 = weight_variable([3, 3, 64, 64])
    b_conv5 = bias_variable([64])
    h_conv5 = tf.nn.relu(conv2d(h_conv4, W_conv5, 1) + b_conv5)
    logging.info(f"Conv5 shape: {h_conv5.shape}")

    # Ajustement de la taille pour obtenir exactement 1156 valeurs
    shape = h_conv5.get_shape().as_list()
    target_height = 17  # Pour obtenir 1156 (17 * 68 = 1156)
    target_width = 68
    h_conv5_resized = tf.image.resize(h_conv5, [target_height, target_width], method='bilinear')
    logging.info(f"Resized shape: {h_conv5_resized.shape}")

    #FCL 1
    h_conv5_flat = tf.reshape(h_conv5_resized, [-1, 1156])
    W_fc1 = weight_variable([1156, 1164])
    b_fc1 = bias_variable([1164])
    h_fc1 = tf.nn.relu(tf.matmul(h_conv5_flat, W_fc1) + b_fc1)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    #FCL 2
    W_fc2 = weight_variable([1164, 100])
    b_fc2 = bias_variable([100])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)
    h_fc2_drop = tf.nn.dropout(h_fc2, keep_prob)

    #FCL 3
    W_fc3 = weight_variable([100, 50])
    b_fc3 = bias_variable([50])
    h_fc3 = tf.nn.relu(tf.matmul(h_fc2_drop, W_fc3) + b_fc3)
    h_fc3_drop = tf.nn.dropout(h_fc3, keep_prob)

    #FCL 4
    W_fc4 = weight_variable([50, 10])
    b_fc4 = bias_variable([10])
    h_fc4 = tf.nn.relu(tf.matmul(h_fc3_drop, W_fc4) + b_fc4)
    h_fc4_drop = tf.nn.dropout(h_fc4, keep_prob)

    #Output
    W_fc5_steering = weight_variable([10, 1])
    b_fc5_steering = bias_variable([1])
    W_fc5_speed = weight_variable([10, 1])
    b_fc5_speed = bias_variable([1])
    W_fc5_throttle = weight_variable([10, 1])
    b_fc5_throttle = bias_variable([1])
    W_fc5_brake = weight_variable([10, 1])
    b_fc5_brake = bias_variable([1])

    y_steering = tf.multiply(tf.atan(tf.matmul(h_fc4_drop, W_fc5_steering) + b_fc5_steering), 2)
    y_speed = tf.nn.sigmoid(tf.matmul(h_fc4_drop, W_fc5_speed) + b_fc5_speed) * 200
    y_throttle = tf.nn.sigmoid(tf.matmul(h_fc4_drop, W_fc5_throttle) + b_fc5_throttle)
    y_brake = tf.nn.sigmoid(tf.matmul(h_fc4_drop, W_fc5_brake) + b_fc5_brake)

    return tf.concat([y_steering, y_speed, y_throttle, y_brake], axis=1)
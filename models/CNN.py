import gym
import numpy as np
import random
import tensorflow as tf
from ..config import params
# import matplotlib.pyplot as plt
from scipy.misc import imresize, imsave
from itertools import chain
from ..models.modelBase import modelBase
from ..models.DQNBaseModel import DQNBaseModel
from functools import reduce
from tensorflow.contrib.layers.python.layers import initializers




WIDTH = 84
class CNN(DQNBaseModel):

	def preprocess(self, frame):
		#TODO divid pixels by 255
		data = np.dot(frame, [0.2126, 0.7152, 0.0722]).astype(np.uint8)
		return imresize(data, (WIDTH, WIDTH))/255.0

	def defineInput(self):
	 	return tf.placeholder(shape=[None, WIDTH, WIDTH, params.stacked_frame_size],dtype=tf.float32, name="X")

#TODO exponensial decay
	def defineTrainer(self):
		return tf.train.RMSPropOptimizer(
            		learning_rate = params.learning_rate,
           			epsilon=0.01,
            		momentum=0.95)

	def defineNNArchitecture(self):
		l1, w1, b1 = self.conv2d(self.X, 32, [8, 8], [4, 4], name='l1')
		l2, w2, b2 = self.conv2d(l1, 64, [4, 4], [2, 2], name='l2')
		l3, w3, b3 = self.conv2d(l2, 64, [3, 3], [1, 1], name='l3')
		shape = l3.get_shape().as_list()
		l3_flat = tf.reshape(l3, [-1, reduce(lambda x, y: x * y, shape[1:])])
		l4, w4, b4 = self.linear(l3_flat, 256, activation_fn=tf.nn.relu, name='l4')
		self.Qprime, w5, b5 = self.linear(l4, self.output_size, name='l5')
		self.P = tf.argmax(self.Qprime, 1)
		self.Qmean = tf.reduce_mean(tf.reduce_max(self.Qprime,axis = 1))
		self.QmeanSummary = tf.summary.scalar("Qmean", self.Qmean)
		self.weights = [w1, b1, w2, b2, w3, b3, w4, b4, w5, b5]

	def conv2d(self, x, output_dim, kernel_size, stride, name):
		data_format='NHWC'
		with tf.variable_scope(name):
			stride = [1, stride[0], stride[1], 1]
			kernel_shape = [kernel_size[0], kernel_size[1], x.get_shape()[-1], output_dim]
			w = tf.get_variable('w', kernel_shape, tf.float32, initializer=tf.truncated_normal_initializer(0, 0.02))
			conv = tf.nn.conv2d(x, w, stride, "VALID", data_format=data_format)
			b = tf.get_variable('biases', [output_dim], initializer=tf.constant_initializer(0.0))
			out = tf.nn.bias_add(conv, b, data_format)
			out = tf.nn.relu(out)
		return out, w, b

	def linear(self, input_, output_size, activation_fn=None, name='linear'):
		shape = input_.get_shape().as_list()
		with tf.variable_scope(name):
			w = tf.get_variable('W', [shape[1], output_size], tf.float32, tf.truncated_normal_initializer(0, 0.02))
			b = tf.get_variable('B', [output_size], initializer=tf.constant_initializer(0.0))
			out = tf.nn.bias_add(tf.matmul(input_, w), b)
		if activation_fn != None:
			return activation_fn(out), w, b
		else:
			return out, w, b

import keras
from keras import regularizers
from keras.models import  Model, Sequential
from keras.layers import Dense, Input, BatchNormalization
from keras.callbacks import EarlyStopping
from sklearn.svm import OneClassSVM

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def svm_auto(train_dataset,test_dataset,threshold):
	clf = OneClassSVM(gamma='auto')
	clf.fit(train_dataset['x'])
	pred = clf.predict(train_dataset['x'])

	p1 = train_dataset['x'][pred==1]
	p2 = train_dataset['x'][pred==-1]

	# NN Autoencoder model.
	input_dim = p1.shape[1]
	input = Input(shape=(input_dim, ))
	encode = Dense(input_dim//3*2, activation='relu',kernel_regularizer=regularizers.l2(0.01))(input)
	encode = BatchNormalization()(encode)
	encode = Dense(input_dim//3, activation='relu',kernel_regularizer=regularizers.l2(0.01))(encode)
	encode = BatchNormalization()(encode)

	decode = Dense(input_dim//3, activation='relu')(encode)
	decode = BatchNormalization()(decode)
	decode = Dense(input_dim//3*2, activation='relu')(decode)
	decode = BatchNormalization()(decode)
	decode = Dense(input_dim, activation='sigmoid')(decode)

	autoencoder = Model(input, decode)

	early_stopping = EarlyStopping(monitor='loss', mode='min')

	autoencoder.compile(optimizer='adam',
											loss='mse',
											metrics=['accuracy'])

	# Train model.
	history = autoencoder.fit(p1, p1,
					epochs=100,
					batch_size=128,
					shuffle=True,
					callbacks = [early_stopping]
					)

	# plot the training losses
	fig, loss_ax  = plt.subplots(figsize=(14, 6), dpi=80)
	acc_ax = loss_ax.twinx()
	loss_ax.plot(history.history['loss'], 'b', label='Train loss', linewidth=2)
	loss_ax.set_xlabel('Epoch')
	loss_ax.set_ylabel('Loss (mae)')
	
	acc_ax.plot(history.history['accuracy'], 'b', label='Train acc', linewidth=2)
	acc_ax.set_ylabel('Accuracy')

	loss_ax.set_title('Model loss,acc', fontsize=16)
	plt.legend(loc='upper right')
	plt.savefig('./result/svm_auto_loss.png')

	# plot the loss distribution of the training set
	X_pred = autoencoder.predict(train_dataset['x'])
	X_pred = pd.DataFrame(X_pred)

	train_scored = pd.DataFrame()
	Xtrain = train_dataset['x']
	train_scored['Loss_mae'] = np.mean(np.abs(X_pred-Xtrain), axis = 1)
	plt.figure(figsize=(16,9), dpi=80)
	plt.title('Loss Distribution', fontsize=16)
	sns.distplot(train_scored['Loss_mae'], bins = 20, kde= True, color = 'blue');
	plt.xlim([0.0,.5])
	plt.savefig('./result/svm_auto_loss_mae.png')

	# calculate the same metrics for the training set 
	# and merge all data in a single dataframe for plotting
	X_pred_train = autoencoder.predict(train_dataset['x'])
	X_pred_train = pd.DataFrame(X_pred_train)

	scored_train = pd.DataFrame()
	scored_train['Loss_mae'] = np.mean(np.abs(X_pred_train-Xtrain), axis = 1)
	scored_train['Threshold'] = scored_train.quantile(threshold)[0]
	scored_train['Anomaly'] = scored_train['Loss_mae'] > scored_train['Threshold']

	# calculate the loss on the test set
	X_pred = autoencoder.predict(test_dataset['x'])
	X_pred = pd.DataFrame(X_pred)

	scored = pd.DataFrame()
	Xtest = test_dataset['x']
	scored['Loss_mae'] = np.mean(np.abs(X_pred-Xtest), axis = 1)
	scored['Threshold'] =  scored_train.quantile(threshold)[0]
	scored['Anomaly'] = scored['Loss_mae'] > scored['Threshold']
	scored.head()

	# scored = pd.concat([scored_train, scored])
	# ture_ = pd.Series(train_dataset['y']).append(pd.Series(test_dataset['y']))
	ture_ = pd.Series(test_dataset['y'])

	return ture_,scored['Anomaly']
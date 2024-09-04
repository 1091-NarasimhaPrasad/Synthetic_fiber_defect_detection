# -*- coding: utf-8 -*-
"""logistic reg.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TYAaP_0ppbyYJJSiUCDbHhrNF1-tXWwi
"""

import os
import cv2
import numpy as np
import pandas as pd
import shutil
import tensorflow as tf
import tensorflow_hub as hub

from sklearn.model_selection import train_test_split
from tensorflow import keras
from keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE
from sklearn.utils import shuffle

from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout


def split_dataset(source_folder, output_root_folder):
    # creating output folders if they don't exist
    target_defect_folder = os.path.join(output_root_folder, "Defect_images")
    target_no_defect_folder = os.path.join(output_root_folder, "NODefect_images")
    os.makedirs(target_defect_folder, exist_ok=True)
    os.makedirs(target_no_defect_folder, exist_ok=True)

    # split defect images
    defect_images_folder = os.path.join(source_folder, "Defect_images")

    # copy defect images
    for file_name in os.listdir(defect_images_folder):
        source_path = os.path.join(defect_images_folder, file_name)
        target_path = os.path.join(target_defect_folder, file_name)
        shutil.copy2(source_path, target_path)

    # copy non-defect images
    no_defect_images_folder = os.path.join(source_folder, "NODefect_images")
    for subfolder_name in os.listdir(no_defect_images_folder):
        subfolder_path = os.path.join(no_defect_images_folder, subfolder_name)
        if os.path.isdir(subfolder_path):
            for file_name in os.listdir(subfolder_path):
                source_path = os.path.join(subfolder_path, file_name)
                target_path = os.path.join(target_no_defect_folder, file_name)
                shutil.copy2(source_path, target_path)

# source folder and the output root directory
dataset_folder = "/content/drive/MyDrive/textile"
output_root_folder = "/content/drive/MyDrive/output feed"


split_dataset(dataset_folder, output_root_folder)





def preprocess_data(defect_folder, nodefect_folder):
    defect_images = load_images_from_folder(defect_folder)
    nodefect_images = load_images_from_folder(nodefect_folder)

    # augmentation
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        brightness_range=[0.8, 1.2]
    )

    augmented_images = []
    for img in defect_images:
        augmented_images.append(img)
        img = np.expand_dims(img, axis=0)
        it = datagen.flow(img, batch_size=1)
        for _ in range(4):  # 4 augmented images per original image
            batch = it.next()
            augmented_img = batch[0].astype('uint8')
            augmented_images.append(augmented_img)

    # combine defect and non-defect images
    X = np.concatenate((augmented_images, nodefect_images))
    y = np.concatenate((np.ones(len(augmented_images)), np.zeros(len(nodefect_images))))

    # shuffle
    X, y = shuffle(X, y, random_state=57)

    return X, y

def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder, filename))
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (224, 224))
            images.append(img)
    return images



def plot_class_distribution(y):
    unique, counts = np.unique(y, return_counts=True)
    labels = ['Defect', 'No Defect']
    plt.pie(counts, labels=labels, autopct='%1.1f%%')
    plt.title('Class Distribution')
    plt.show()




defect_folder = os.path.join(output_root_folder, "Defect_images")
nodefect_folder = os.path.join(output_root_folder, "NODefect_images")

X, y = preprocess_data(defect_folder, nodefect_folder)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=57)


plot_class_distribution(y_train)



smote = SMOTE(random_state=57)
X_train, y_train = smote.fit_resample(X_train.reshape(-1, 224 * 224 * 3), y_train)

X_train = X_train.reshape(-1, 224, 224, 3)

plot_class_distribution(y_train)

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Flatten the input matrices
X_train_flatten = X_train.reshape(X_train.shape[0], -1)
X_test_flatten = X_test.reshape(X_test.shape[0], -1)
# Separate variables for initial training data
X_train_initial = X_train_flatten.copy()
y_train_initial = y_train.copy()

# Set the number of iterations for repeated train/test splits
num_iterations = 10
accuracy_scores = []

for i in range(num_iterations):
    # Split the initial training data into train and validation sets
    X_train, X_val, y_train, y_val = train_test_split(X_train_initial, y_train_initial, test_size=0.2, random_state=i)

    # Initialize and train the logistic regression model
    logistic_model = LogisticRegression(solver='lbfgs', max_iter=1000)
    logistic_model.fit(X_train, y_train)

    # Make predictions on the validation set
    y_pred = logistic_model.predict(X_val)

    # Calculate and store the accuracy score for this iteration
    accuracy = accuracy_score(y_val, y_pred)
    accuracy_scores.append(accuracy)

    # Print the accuracy for each iteration
    print(f"Iteration {i + 1}: Accuracy = {accuracy}")

# Convert the accuracy scores list to a DataFrame
accuracy_df = pd.DataFrame({'Accuracy': accuracy_scores})
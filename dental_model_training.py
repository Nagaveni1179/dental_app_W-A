{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Dental AI - Image Classification Model Training Notebook\n",
    "\n",
    "This notebook trains a Transfer Learning model using **MobileNetV2** and **TensorFlow / Keras** to classify dental conditions from images.\n",
    "\n",
    "### Target Classes:\n",
    "- Calculus\n",
    "- Data caries\n",
    "- Gingivitis\n",
    "- Hypodontia\n",
    "- Mouth Ulcer\n",
    "- Tooth Discoloration\n",
    "\n",
    "### Outputs Generated:\n",
    "1. `dental_model.h5` - Trained TensorFlow/Keras model artifact.\n",
    "2. `class_names.json` - JSON mapping of dataset class indices to labels."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 1: Mount Google Drive\n",
    "Mount your Google Drive to access the dataset stored at `/content/drive/MyDrive/dataset`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from google.colab import drive\n",
    "import os\n",
    "\n",
    "# Mount Google Drive\n",
    "drive.mount('/content/drive')\n",
    "\n",
    "# Define dataset directory path\n",
    "DATASET_DIR = '/content/drive/MyDrive/dataset'\n",
    "\n",
    "if os.path.exists(DATASET_DIR):\n",
    "    print(f\"✅ Dataset folder found at: {DATASET_DIR}\")\n",
    "    print(\"Detected folders:\", sorted(os.listdir(DATASET_DIR)))\n",
    "else:\n",
    "    print(f\"❌ ERROR: Folder {DATASET_DIR} does not exist! Please check your Drive path.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 2: Import Libraries\n",
    "Import necessary packages for deep learning, data manipulation, and visualization."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import json\n",
    "import matplotlib.pyplot as plt\n",
    "import numpy as np\n",
    "import tensorflow as tf\n",
    "from tensorflow.keras import layers, models\n",
    "from tensorflow.keras.applications import MobileNetV2\n",
    "from google.colab import files\n",
    "\n",
    "print(f\"TensorFlow version: {tf.__version__}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 3: Define Parameters & Load Dataset\n",
    "- **Image Size**: 224 x 224 (required input size for MobileNetV2)\n",
    "- **Batch Size**: 32\n",
    "- **Train/Val Split**: 80% Training, 20% Validation"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "IMG_SIZE = (224, 224)\n",
    "BATCH_SIZE = 32\n",
    "EPOCHS = 15\n",
    "SEED = 42\n",
    "\n",
    "# Load Training Dataset (80% split)\n",
    "train_ds = tf.keras.utils.image_dataset_from_directory(\n",
    "    DATASET_DIR,\n",
    "    validation_split=0.2,\n",
    "    subset=\"training\",\n",
    "    seed=SEED,\n",
    "    image_size=IMG_SIZE,\n",
    "    batch_size=BATCH_SIZE\n",
    ")\n",
    "\n",
    "# Load Validation Dataset (20% split)\n",
    "val_ds = tf.keras.utils.image_dataset_from_directory(\n",
    "    DATASET_DIR,\n",
    "    validation_split=0.2,\n",
    "    subset=\"validation\",\n",
    "    seed=SEED,\n",
    "    image_size=IMG_SIZE,\n",
    "    batch_size=BATCH_SIZE\n",
    ")\n",
    "\n",
    "# Automatically detect class names\n",
    "class_names = train_ds.class_names\n",
    "NUM_CLASSES = len(class_names)\n",
    "\n",
    "print(\"\\n--- Dataset Summary ---\")\n",
    "print(f\"Detected {NUM_CLASSES} classes: {class_names}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 4: Save Class Names to JSON\n",
    "Save the list of detected class names as `class_names.json` to be used by the Flask backend or Flutter app for inference mapping."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "with open('class_names.json', 'w') as f:\n",
    "    json.dump(class_names, f, indent=4)\n",
    "\n",
    "print(\"Saved class names to class_names.json:\")\n",
    "print(json.dumps(class_names, indent=2))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 5: Data Augmentation & Performance Optimization\n",
    "Add random flips, rotations, and zoom transformations to reduce overfitting and improve generalization on dental images."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "data_augmentation = tf.keras.Sequential([\n",
    "    layers.RandomFlip(\"horizontal_and_vertical\"),\n",
    "    layers.RandomRotation(0.2),\n",
    "    layers.RandomZoom(0.2),\n",
    "    layers.RandomContrast(0.1)\n",
    "], name=\"data_augmentation\")\n",
    "\n",
    "# Optimize dataset performance with prefetching and caching\n",
    "AUTOTUNE = tf.data.AUTOTUNE\n",
    "train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)\n",
    "val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 6: Build Model Architecture (MobileNetV2 Transfer Learning)\n",
    "1. Load pre-trained **MobileNetV2** weights (trained on ImageNet) without top classification head.\n",
    "2. Preprocess inputs using `preprocess_input` (normalizes pixels to [-1, 1]).\n",
    "3. Add Data Augmentation, Global Average Pooling, Dropout, and Dense output layer with Softmax activation."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from tensorflow.keras.applications.mobilenet_v2 import preprocess_input\n",
    "\n",
    "# Load MobileNetV2 base model pre-trained on ImageNet\n",
    "base_model = MobileNetV2(\n",
    "    input_shape=IMG_SIZE + (3,),\n",
    "    include_top=False,\n",
    "    weights='imagenet'\n",
    ")\n",
    "\n",
    "# Freeze base model feature extractor weights\n",
    "base_model.trainable = False\n",
    "\n",
    "# Build full classification model pipeline\n",
    "inputs = layers.Input(shape=IMG_SIZE + (3,))\n",
    "x = data_augmentation(inputs)\n",
    "x = preprocess_input(x)  # Normalizes [0, 255] pixels to [-1, 1] for MobileNetV2\n",
    "x = base_model(x, training=False)\n",
    "x = layers.GlobalAveragePooling2D()(x)\n",
    "x = layers.Dropout(0.2)(x)\n",
    "outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)\n",
    "\n",
    "model = models.Model(inputs, outputs, name=\"Dental_MobileNetV2\")\n",
    "\n",
    "model.compile(\n",
    "    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),\n",
    "    loss='sparse_categorical_crossentropy',\n",
    "    metrics=['accuracy']\n",
    ")\n",
    "\n",
    "model.summary()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 7: Train the Model\n",
    "Train the model for 15 epochs on the dental dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "history = model.fit(\n",
    "    train_ds,\n",
    "    validation_data=val_ds,\n",
    "    epochs=EPOCHS\n",
    ")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 8: Visualize Training & Validation Metrics\n",
    "Plot Accuracy and Loss curves to evaluate convergence and performance over 15 epochs."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "acc = history.history['accuracy']\n",
    "val_acc = history.history['val_accuracy']\n",
    "loss = history.history['loss']\n",
    "val_loss = history.history['val_loss']\n",
    "\n",
    "epochs_range = range(EPOCHS)\n",
    "\n",
    "plt.figure(figsize=(14, 5))\n",
    "\n",
    "# Accuracy Plot\n",
    "plt.subplot(1, 2, 1)\n",
    "plt.plot(epochs_range, acc, label='Training Accuracy', marker='o')\n",
    "plt.plot(epochs_range, val_acc, label='Validation Accuracy', marker='o')\n",
    "plt.title('Training and Validation Accuracy')\n",
    "plt.xlabel('Epoch')\n",
    "plt.ylabel('Accuracy')\n",
    "plt.legend(loc='lower right')\n",
    "plt.grid(True)\n",
    "\n",
    "# Loss Plot\n",
    "plt.subplot(1, 2, 2)\n",
    "plt.plot(epochs_range, loss, label='Training Loss', marker='o')\n",
    "plt.plot(epochs_range, val_loss, label='Validation Loss', marker='o')\n",
    "plt.title('Training and Validation Loss')\n",
    "plt.xlabel('Epoch')\n",
    "plt.ylabel('Loss')\n",
    "plt.legend(loc='upper right')\n",
    "plt.grid(True)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 9: Model Evaluation\n",
    "Evaluate final loss and accuracy on the validation dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "val_loss_final, val_acc_final = model.evaluate(val_ds)\n",
    "print(f\"\\nFinal Validation Loss:     {val_loss_final:.4f}\")\n",
    "print(f\"Final Validation Accuracy: {val_acc_final * 100:.2f}%\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 10: Save Trained Model\n",
    "Save model weights and structure to `dental_model.h5`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "MODEL_FILE = 'dental_model.h5'\n",
    "model.save(MODEL_FILE)\n",
    "print(f\"✅ Model successfully saved to: {MODEL_FILE}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 11: Automatically Download Files\n",
    "Automatically trigger browser download for both `dental_model.h5` and `class_names.json`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"Downloading model file and class names...\")\n",
    "files.download('dental_model.h5')\n",
    "files.download('class_names.json')\n",
    "print(\"✅ Download triggered automatically!\")"
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

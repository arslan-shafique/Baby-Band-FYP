import tensorflow as tf
from tensorflow.keras.layers import Conv2D, BatchNormalization, ReLU, MaxPooling2D, Dropout, Reshape, MultiHeadAttention, LSTM, Dense, Input, Permute, LayerNormalization, Add, GlobalAveragePooling1D
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam

class SparseCategoricalFocalLoss(tf.keras.losses.Loss):
    """
    Custom implementation of Focal Loss that accepts sparse (integer) targets.
    This avoids having to modify train.py or evaluate.py to use one-hot encoding.
    """
    def __init__(self, gamma=2.0, alpha=0.25, **kwargs):
        super().__init__(**kwargs)
        self.gamma = gamma
        self.alpha = alpha

    def call(self, y_true, y_pred):
        y_true = tf.cast(tf.reshape(y_true, [-1]), tf.int32)
        num_classes = tf.shape(y_pred)[-1]
        y_true_one_hot = tf.one_hot(y_true, depth=num_classes)
        
        # Clip predictions to prevent log(0)
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1.0 - tf.keras.backend.epsilon())
        
        # Calculate standard Cross Entropy
        ce = -y_true_one_hot * tf.math.log(y_pred)
        
        # Calculate Focal Loss modifier
        weight = tf.math.pow(1.0 - y_pred, self.gamma)
        focal_loss = self.alpha * weight * ce
        
        return tf.reduce_sum(focal_loss, axis=-1)

def build_model(input_shape=(128, 128, 1), num_classes=4, batch_size=None):
    inputs = Input(shape=input_shape, batch_size=batch_size)
    x = inputs
    
    # --- 1. CNN Base ---
    filters = [16, 32, 64, 64] 
    for f in filters:
        x = Conv2D(f, kernel_size=(5, 5), strides=(1, 1), padding='same', kernel_regularizer=l2(1e-4))(x)
        x = BatchNormalization()(x)
        x = ReLU()(x)
        x = MaxPooling2D(pool_size=(2, 2), padding='same')(x)
        x = Dropout(0.3)(x)
        
    # --- 2. The Reshape ---
    shape = x.shape
    # Transpose to (None, Time, Freq, Channels) -> (None, 8, 8, 64)
    x = Permute((2, 1, 3))(x) 
    # Flatten frequency and channels into a single feature vector per timestep
    x = Reshape((-1, shape[1] * shape[3]))(x) # (None, 8, 512)
    
    # --- 3. Stacked LSTMs ---
    x = LSTM(128, return_sequences=True)(x)
    x = LSTM(64, return_sequences=False)(x)
    x = Dropout(0.3)(x)
    
    # --- 4. Classifier ---
    outputs = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs, outputs)
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss=SparseCategoricalFocalLoss(alpha=0.25, gamma=2.0),
        metrics=['accuracy']
    )
    
    return model

if __name__ == "__main__":
    model = build_model()
    model.summary()
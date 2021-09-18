from os.path import join

import numpy as np

import tensorflow as tf


class AudioClassifierCNN:
    def __init__(self, model_directory: str) -> None:
        self.model: tf.keras.Model = tf.keras.models.load_model(model_directory)
        self.labels = np.load(open(join(model_directory, "labels.npy"), "rb"))
        self.AUTOTUNE = tf.data.AUTOTUNE

    def _get_spectrogram(self, waveform):
        # Padding for files with less than 16000 samples
        zero_padding = tf.zeros([65000] - tf.shape(waveform), dtype=tf.float32)
        # Concatenate audio with padding so that all audio clips will be of the
        # same length
        waveform = tf.cast(waveform, tf.float32)
        equal_length = tf.concat([waveform, zero_padding], 0)
        spectrogram = tf.signal.stft(equal_length, frame_length=255, frame_step=128)

        spectrogram = tf.abs(spectrogram)

        return spectrogram

    def decode_audio(self, file):
        audio_binary = file.read()
        file.seek(0)
        audio, _ = tf.audio.decode_wav(audio_binary)
        return tf.squeeze(audio, axis=-1)

    def get_waveform(self, file):
        waveform = self.decode_audio(file)
        return waveform

    def get_spectrogram(self, audio):
        spectrogram = self._get_spectrogram(audio)
        spectrogram = tf.expand_dims(spectrogram, -1)
        return spectrogram

    def preprocess(self, file):
        waveform = self.get_waveform(file)
        return self.get_spectrogram(waveform)

    def predict(self, file, answer):
        spectrogram = self.preprocess(file)
        predictions = self.model(tf.expand_dims(spectrogram, 0))
        prediction = tf.nn.softmax(predictions[0]).numpy()
        top_predictions = prediction.argsort()[::-1][:5]
        if self.labels[top_predictions[0]] == answer:
            return True
        else:
            return False
        # return [
        #     {"label": self.labels[i], "match": prediction[i].item(), "is_matched": True}
        #     for i in top_predictions
        # ]


AudioClassifier = AudioClassifierCNN("./models/classifier250")
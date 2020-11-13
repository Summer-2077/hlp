import matplotlib.pyplot as plt
import scipy.io.wavfile as wave
import tensorflow as tf
import numpy as np
from playsound import playsound

from config2 import Tacotron2Config
from prepocesses import dataset_txt, get_tokenizer_keras
from tacotron2 import Tacotron2, load_checkpoint
from audio_process import melspectrogram2wav


# 下面两个方法没使用，暂时保留
def _plot_spectrogram_to_numpy(spectrogram):
    fig, ax = plt.subplots(figsize=(12, 3))
    im = ax.imshow(spectrogram, aspect="auto", origin="lower",
                   interpolation='none')
    plt.colorbar(im, ax=ax)
    plt.xlabel("Frames")
    plt.ylabel("Channels")
    plt.tight_layout()
    fig.canvas.draw()
    data = _save_figure_to_numpy(fig)
    plt.close()
    return data


def _save_figure_to_numpy(fig):
    # 保存成numpy
    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return data


if __name__ == "__main__":
    config = Tacotron2Config()
    # 检查点路径
    path = config.checkpoingt_dir

    # 字典路径
    save_path_dictionary = config.save_path_dictionary_number

    # 恢复字典
    tokenizer, vocab_size = get_tokenizer_keras(save_path_dictionary)
    print("vocab_size:", vocab_size)

    # 模型初始化
    tacotron2 = Tacotron2(vocab_size + 1, config)

    # 加载检查点
    checkpoint = load_checkpoint(tacotron2, path, config)
    print('已恢复至最新的检查点！')

    # 抓取文本数据
    print("请输入需要合成的话：")
    seq = input()
    sequences_list = []
    sequences_list.append(seq)
    input_ids, vocab_inp_size = dataset_txt(sequences_list, save_path_dictionary, "predict")
    input_ids = tf.convert_to_tensor(input_ids)

    # 预测
    mel_outputs, mel_outputs_postnet, gate_outputs, alignments = tacotron2.inference(input_ids)

    # 生成预测声音
    wav = melspectrogram2wav(mel_outputs_postnet[0].numpy(), config.max_db, config.ref_db, config.sr, config.n_fft, config.n_mels, config.preemphasis, config.n_iter, config.hop_length, config.win_length)

    wave.write('generated.wav', rate=config.sr, data=wav)
    playsound('.\generated.wav')
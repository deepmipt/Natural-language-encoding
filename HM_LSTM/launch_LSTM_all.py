import numpy as np
import tensorflow as tf
from six.moves import range
from six.moves.urllib.request import urlretrieve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import codecs
import time
import os
import gc
from six.moves import cPickle as pickle
import sys
import subprocess
if not os.path.isfile('model_module.py') or not os.path.isfile('plot_module.py'):
    current_path = os.path.dirname(os.path.abspath('__file__'))
    additional_path = '/'.join(current_path.split('/')[:-1])
    sys.path.append(additional_path)
from plot_module import text_plot
from plot_module import structure_vocabulary_plots
from plot_module import text_boundaries_plot
from plot_module import ComparePlots

from model_module import maybe_download
from model_module import read_data
from model_module import create_vocabulary
from model_module import get_positions_in_vocabulary
from model_module import filter_text
from model_module import check_not_one_byte
from model_module import id2char
from model_module import char2id
from model_module import BatchGenerator
from model_module import characters
from model_module import batches2string
from model_module import logprob
from model_module import sample_distribution


version = sys.version_info[0]

class CommandLineInput(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

if sys.argv[1] == 'LSTM_all':
    from LSTM_all_core import LSTM
elif sys.argv[1] == 'LSTM_stacked':
    from LSTM_stacked_core import LSTM


if len(sys.argv) < 3:
    raise CommandLineInput("3rd command line argument indicating dataset type is missing.\nUse either 'clean' or 'dirty'")
if sys.argv[2] == 'dirty':
    if not os.path.exists('enwik8_filtered'):
        if not os.path.exists('enwik8'):
            filename = maybe_download('enwik8.zip', 36445475)
            full_text = read_data(filename)
            f = open('enwik8', 'wb')
            f.write(full_text.encode('utf8'))
            f.close()
        else:
            f = open('enwik8', 'rb')
            full_text = f.read().decode('utf8')
            f.close()
        new_text = u""
        new_text_list = list()
        for i in range(len(full_text)):
            if (i+1) % 10000000 == 0:
                print("%s characters are filtered" % i)
            if ord(full_text[i]) < 256:
                new_text_list.append(full_text[i])
        text = new_text.join(new_text_list)
        del new_text_list
        del new_text
        del full_text

        (not_one_byte_counter, min_character_order_index, max_character_order_index, number_of_characters, present_characters_indices) = check_not_one_byte(text)

        print("number of not one byte characters: ", not_one_byte_counter) 
        print("min order index: ", min_character_order_index)
        print("max order index: ", max_character_order_index)
        print("total number of characters: ", number_of_characters)
    
        f = open('enwik8_filtered', 'wb')
        f.write(text.encode('utf8'))
        f.close()
    
    else:

        f = open('enwik8_filtered', 'rb')
        text = f.read().decode('utf8')
        f.close() 
        (not_one_byte_counter, min_character_order_index, max_character_order_index, number_of_characters, present_characters_indices) = check_not_one_byte(text)
elif sys.argv[2] == 'clean':
    if not os.path.exists('enwik8_clean'):
        if not os.path.exists('enwik8'):
            filename = maybe_download('enwik8.zip', 36445475)
            full_text = read_data(filename)
            f = open('enwik8', 'wb')
            f.write(full_text.encode('utf8'))
            f.close()       
        perl_script = subprocess.call(['perl', "clean.pl", 'enwik8', 'enwik8_clean'])
    f = open('enwik8_clean', 'rb')
    text = f.read().decode('utf8')
    print(len(text))
    f.close() 
    (not_one_byte_counter, min_character_order_index, max_character_order_index, number_of_characters, present_characters_indices) = check_not_one_byte(text)

else:
    f = open(sys.argv[2], 'r', encoding='utf-8')
    text = f.read()
    f.close() 



#different
offset = 20000
valid_size = 10000
valid_text = text[offset:offset+valid_size]
train_text = text[offset+valid_size:]
train_size = len(train_text)


# In[5]:


vocabulary = create_vocabulary(text)
vocabulary_size = len(vocabulary)
characters_positions_in_vocabulary = get_positions_in_vocabulary(vocabulary)
print(vocabulary)

num_nodes = 12
model_type = sys.argv[1]
experiment_name = 'effectiveness_clean_long'
model = LSTM(64,
                 vocabulary,
                 characters_positions_in_vocabulary,
                 30,
                 3,
                 [num_nodes, num_nodes, num_nodes],
                 train_text,
                 valid_text,
                init_parameter=1e-6,
                 matr_init_parameter=100000)


model.run(8,                # number of times learning_rate is decreased
          0.5,              # a factor by which learning_rate is decreased
            1000,            # each 'train_frequency' steps loss and percent correctly predicted letters is calculated
            200,             # minimum number of times loss and percent correctly predicted letters are calculated while learning (train points)
            3,              # if during half total spent time loss decreased by less than 'stop_percent' percents learning process is stopped
            1,              # when train point is obtained validation may be performed
            3,             # when train point percent is calculated results got on averaging_number chunks are averaged
          fixed_number_of_steps=200001,
          validation_example_length=40, 
           #debug=True,
            print_intermediate_results = True,
          path_to_file_for_saving_prints='peganov/' + model_type +'/'+ experiment_name + '/effectiveness_clean.txt',
           save_path='peganov/' + model_type +'/'+ experiment_name + '/variables',
           gpu_memory=1.)
results_GL = list(model._results)

folder_name = 'peganov/' + model_type +'/'+ experiment_name
file_name = experiment_name + '_result.pickle'
force = True
pickle_dump = {'results_GL': results_GL}
if not os.path.exists(folder_name):
    try:
        os.makedirs(folder_name)
    except Exception as e:
        print("Unable create folder '%s'" % folder_name, ':', e)    
print('Pickling %s' % (folder_name + '/' + file_name))
try:
    with open(folder_name + '/' + file_name, 'wb') as f:
        pickle.dump(pickle_dump, f, pickle.HIGHEST_PROTOCOL)
except Exception as e:
    print('Unable to save data to', file_name, ':', e)

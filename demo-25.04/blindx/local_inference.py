# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import blindx.misc as misc
from blindx.text_wrapper import TextWrapper
from transformers import T5ForConditionalGeneration, T5Tokenizer

import os
import asyncio
import torch
import logging

# クライアントから指定できる推論パラメータの上限
MAX_NUM_BEAMS = 8
MAX_LENGTH = 256
MAX_INPUT_LENGTH = 1024

# 追加引数 (key=value,...) として generate() に渡してよいもの
ALLOWED_GENERATE_ARGS = {
    'early_stopping', 'return_legacy_cache', 'length_penalty',
    'no_repeat_ngram_size', 'repetition_penalty', 'max_length',
}

class LocalInference():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'

        self.target_dir = misc.search_path('models')
        self.t5_names = [name for name in os.listdir(self.target_dir) if 'all' in name]
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.logger.info(f'torch: version={torch.__version__} device={self.device}')
        self.tokenizer = T5Tokenizer.from_pretrained('sonoisa/t5-base-japanese-v1.1', legacy=True)
        self.text_wrapper = TextWrapper()

        self.t5s = []
        for t5_name in self.t5_names:
            full_path = os.path.join(self.target_dir, t5_name)
            self.logger.info(f'load {full_path}')
            t5 = T5ForConditionalGeneration.from_pretrained(full_path)
            t5.to(self.device)
            self.t5s.append(t5)

    def translate(self, message):

        try:
            t5_index, input_text, fixed_text, args = self.parse_input_message(message)
            if not input_text: return ''

            input_ids = self.tokenizer(input_text, return_tensors='pt').input_ids.to(self.device)
            decoder_input_ids = self.tokenize_fixed_text(fixed_text)
            t5_outputs = self.t5s[t5_index].generate(
                **args, input_ids = input_ids, decoder_input_ids = decoder_input_ids)

            result_message = self.assemble_output_message(t5_outputs)
            self.report(message, result_message)
            return result_message

        except Exception as e:
            self.logger.error(e)
            errstr = str(e).replace('\n', '\\n').replace(':', ';')
            msgstr = message.replace(':', ';')
            return f'ERROR:むこうなこまんどです:{errstr}:{msgstr}'

    def query(self, message):
        output = ''
        for t5_name in self.t5_names:
            output += t5_name + ':'
        output = output[:-1]    
        self.logger.info(f'query {output}')
        return output

    def parse_input_message(self, message):    
        list = message.split(':')
        com = list[0]
        num_beams = int(list[1])
        if not 1 <= num_beams <= MAX_NUM_BEAMS:
            raise ValueError(f'num_beams must be between 1 and {MAX_NUM_BEAMS}')
        if len(list[2]) > MAX_INPUT_LENGTH:
            raise ValueError(f'input text is too long (max {MAX_INPUT_LENGTH})')
        input_text = self.text_wrapper.encode(list[2])
        fixed_text = ''
        t5_index = int(com[1:])
        if not 0 <= t5_index < len(self.t5s):
            raise ValueError(f'invalid dictionary index {t5_index}')

        args = {
            'max_length': MAX_LENGTH,
            'num_beams': num_beams,
            'num_return_sequences' : num_beams,
        }

        if len(list) > 3:
            fixed_text = list[3]

        if len(list) > 4:
            aux_args = misc.parse_key_value_string(list[4])
            unsupported = sorted(set(aux_args) - ALLOWED_GENERATE_ARGS)
            if unsupported:
                raise ValueError(f'unsupported arguments {unsupported}')
            args |= aux_args

        max_length = args['max_length']
        if isinstance(max_length, bool) or not isinstance(max_length, int) \
                or not 1 <= max_length <= MAX_LENGTH:
            raise ValueError(f'max_length must be between 1 and {MAX_LENGTH}')

        return t5_index, input_text, fixed_text, args

    def tokenize_fixed_text(self, fixed_text):
        if not fixed_text:
            return None

        decoder_input_ids = self.tokenizer(fixed_text, return_tensors='pt').input_ids
        decoder_input_ids_list = decoder_input_ids.tolist()[0]

        truncated_decoder_input_ids_list = []
        for id in decoder_input_ids_list:
            if id == self.tokenizer.eos_token_id:
                break
            truncated_decoder_input_ids_list.append(id)

        return torch.tensor([truncated_decoder_input_ids_list]).to(self.device)

    def assemble_output_message(self, t5_outputs):
        result_text = ''
        for output in t5_outputs:
            output_text = self.text_wrapper.decode(
                self.tokenizer.decode(
                    output, skip_special_tokens = True
                )
            )
            result_text += output_text + ':'

        if result_text:    
            result_text = result_text[:-1]    
        return result_text

    def report(self, input_text, output_text):
        replaced_in = input_text.replace('\n', '\\n')
        replaced_out = output_text.replace('\n', '\\n')
        self.logger.info(f"in:  {replaced_in}") # no backslash inside '{}'
        self.logger.info(f"out: {replaced_out}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass





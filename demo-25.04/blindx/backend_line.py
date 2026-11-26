# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import json

class BackendLine:
    def __init__(self):
        self.key = None
        self.do_short = True
        self.do_long = True
        self.input_text = ''
        self.output_text = ''
        self.stage_input_text = ''
        self.prev_output_text = ''
        self.long_output_text = ''
        self.serialized_text = ''

    def postfix(self):
        return self.input_text[len(self.stage_input_text):]

    def dup(self):
        result = BackendLine()
        result.key = self.key
        result.do_short = self.do_short
        result.do_long =  self.do_long
        result.input_text = str(self.input_text)
        result.output_text = str(self.output_text)
        result.stage_input_text = str(self.stage_input_text)
        result.prev_output_text = str(self.prev_output_text)
        result.long_output_text = str(self.long_output_text)
        result.serialized_text = str(self.serialized_text)
        return result

    def quick_hash(self):
        hashes = tuple(hash(s) for s in (
            self.input_text, 
            self.output_text,
            self.stage_input_text,
            self.prev_output_text,
            self.long_output_text
        ))
        return hash(hashes)

    def report(self, lineno):
        input_text = self.input_text.replace('\n', '\\n')
        stage_input_text = self.stage_input_text.replace('\n', '\\n')
        output_text = self.output_text.replace('\n', '\\n')
        long_output_text = self.long_output_text.replace('\n', '\\n')
        print(f' {lineno}:{self.key}:{input_text}:{stage_input_text}:{output_text}:{long_output_text}')

    # ':' 区切りだと本文に ':' が含まれたとき (バッククォートで囲んだ半角文字など) に
    # 壊れるため、JSON の配列として直列化する
    def serialize(self):
        self.serialized_text = ''
        if self.key:
            self.serialized_text = json.dumps([
                self.key,
                self.input_text,
                self.output_text,
                self.stage_input_text,
                self.prev_output_text,
                self.long_output_text,
            ], ensure_ascii=False)

    def deserialize(self):
        try:
            fields = json.loads(self.serialized_text)
        except ValueError:
            return
        if isinstance(fields, list) and len(fields) == 6 \
                and all(isinstance(field, str) for field in fields):
            (
                self.key,
                self.input_text,
                self.output_text,
                self.stage_input_text,
                self.prev_output_text,
                self.long_output_text,
            ) = fields


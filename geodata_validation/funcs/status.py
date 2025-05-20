



class Infotext():
    def __init__(self, text: str="") -> None:
        self.content = self._set_content(text)
    
    def _set_content(self, text):
        if len(text.strip()) < 2 or text.strip()[-2:] != "\n":
            return text
        else:
            return text + "\n"
            
    def newline(self):
        self.content += "\n"

    def append(self, text: str|None):
        if not text:
            pass
        self.content += f"{text} \n"

    def add_info(self, text: str):
        self.content += f"INFO: {text} \n"

    def add_warning(self, text: str):
        self.content += f"WARNING: {text} \n"

    def add_error(self, text: str):
        self.content += f"ERROR: {text} \n"

    def clear(self):
        self.content = ""



class Result():
    def __init__(self, category: str, analysis: str, geodata_layer: dict={}, info_output: dict={}):
        self.category = category
        self.analysis = analysis
        self.geodata_layer = geodata_layer # dict of keys (names) and values (geodata_layer)
        self.info_output = info_output # dict of keys (names) and values (info)

    def append_geodata(self, name: str, geodata):
        if name not in self.geodata_layer:
            self.geodata_layer[name] = geodata
        else:
            raise ValueError(f"Key name already exists in this dictionary - {self.geodata_layer}")

    def append_info(self, name: str, info):
        if name not in self.info_output:
            self.info_output[name] = info
        else:
            raise ValueError(f"Key name already exists in this dictionary - {self.info_output.keys()}")
    
    def reset_data(self):
        if len(self.geodata_layer) > 0 or len(self.info_output) > 0:
            self.geodata_layer.clear()
            self.info_output.clear()


class AzureBatchRenderJob(object):
    render_engine = "Renderer_Default"

    def __init__(self):
        self._renderer = "DefaultModule"
        self.label = "Default Module"

    def display(self, ui):
        pass

    def delete(self):
        pass

    def render_enabled(self):
        return True

    def get_jobdata(self):
        return ["fileA.txt", "fileB.jpg"]

    def get_title(self):
        return "MyJobTitle"

    def get_params(self):
        return {"setting_A":1, "setting_B":2}

    def disable(self, disabled):
        pass

class AzureBatchRenderAssets(object):
    render_engine = "Renderer_Default"

    def renderer_assets(self):
        return {}

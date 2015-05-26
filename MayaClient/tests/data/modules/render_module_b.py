from default import BatchAppsRenderJob

class BatchAppsModuleBJob(BatchAppsRenderJob):
    render_engine = "Renderer_B"

    def __init__(self):
        self._renderer = "ModuleB"
        self.label = "Module B"

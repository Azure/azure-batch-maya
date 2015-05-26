from default import BatchAppsRenderJob, BatchAppsRenderAssets

class BatchAppsModuleAJob(BatchAppsRenderJob):
    render_engine = "Renderer_A"

    def __init__(self):
        self._renderer = "ModuleA"
        self.label = "Module A"

class BatchAppsModuleAAssets(BatchAppsRenderAssets):
    render_engine = "Renderer_A"

    def renderer_assets(self):
        return {}

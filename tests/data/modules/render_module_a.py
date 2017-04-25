from default import AzureBatchRenderJob, AzureBatchRenderAssets

class AzureBatchModuleAJob(AzureBatchRenderJob):
    render_engine = "Renderer_A"

    def __init__(self):
        self._renderer = "ModuleA"
        self.label = "Module A"

class AzureBatchAModuleAAssets(AzureBatchRenderAssets):
    render_engine = "Renderer_A"

    def renderer_assets(self):
        return {}

from default import AzureBatchRenderJob

class AzureBatchModuleBJob(AzureBatchRenderJob):
    render_engine = "Renderer_B"

    def __init__(self):
        self._renderer = "ModuleB"
        self.label = "Module B"

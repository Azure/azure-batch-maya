from default import AzureBatchRenderAssets

class AzureBatchModuleCAssets(AzureBatchRenderAssets):
    render_engine = "Renderer_C"

    def renderer_assets(self):
        return {}
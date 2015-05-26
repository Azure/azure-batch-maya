from default import BatchAppsRenderAssets

class BatchAppsModuleCAssets(BatchAppsRenderAssets):
    render_engine = "Renderer_C"

    def renderer_assets(self):
        return {}
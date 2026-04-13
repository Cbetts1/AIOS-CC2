"""AI-OS Terminal Panels - Engine status panel."""
from datetime import datetime


class EnginePanel:
    def __init__(self, aura_engine=None):
        self._aura = aura_engine

    def render(self, width: int = 60) -> list:
        lines = []
        lines.append("┌─ AURA ENGINE STATUS " + "─" * (width - 22) + "┐")

        if self._aura is None:
            lines.append(f"│  {'AuraEngine not attached':<{width-3}}│")
            lines.append("└" + "─" * (width - 1) + "┘")
            return lines

        st = self._aura.status()
        lines.append(f"│  Status    : {st.get('status', 'UNKNOWN'):<{width-16}}│")
        lines.append(f"│  Ticks     : {st.get('tick_count', 0):<{width-16}}│")
        lines.append(f"│  Uptime    : {str(st.get('uptime_seconds', 0))+'s':<{width-16}}│")
        lines.append(f"│  {'─'*(width-4)}│")
        lines.append(f"│  Sub-Engines:{'':>{width-16}}│")

        sub = st.get("sub_engines", {})
        for engine_name, engine_st in sub.items():
            healthy = "✓" if engine_st.get("healthy") else "✗"
            ticks = engine_st.get("tick_count", 0)
            label = f"  {healthy} {engine_name:<26} ticks={ticks}"
            lines.append(f"│{label:<{width-1}}│")

        lines.append("└" + "─" * (width - 1) + "┘")
        return lines

    def render_text(self, width: int = 60) -> str:
        return "\n".join(self.render(width))

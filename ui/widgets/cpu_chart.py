from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class CpuChart(FigureCanvasQTAgg):
    def __init__(self):
        figure = Figure(figsize=(7, 3.2), tight_layout=True, facecolor="#0d1119")
        super().__init__(figure)
        self.axes = figure.add_subplot(111)
        self._configure_axes()
        self.line, = self.axes.plot(
            [], [], color="#55d6be", linewidth=2.2, solid_capstyle="round"
        )
        self.latest_point, = self.axes.plot(
            [], [], marker="o", markersize=5, color="#55d6be", linestyle="none"
        )
        self.empty_message = self.axes.text(
            0.5, 0.5, "Ainda não há medições",
            ha="center", va="center", color="#8993a5",
            transform=self.axes.transAxes,
        )

    def update_data(self, rows):
        if not rows:
            self.line.set_data([], [])
            self.latest_point.set_data([], [])
            self.empty_message.set_visible(True)
            self.draw_idle()
            return

        rows = list(reversed(rows))
        values = [row[1] if row[1] is not None else float("nan") for row in rows]
        samples = list(range(len(values)))
        self.line.set_data(samples, values)
        self.empty_message.set_visible(False)

        latest_value = values[-1]
        if latest_value == latest_value:  # NaN is the only value unequal to itself.
            self.latest_point.set_data([samples[-1]], [latest_value])
        else:
            self.latest_point.set_data([], [])

        self.axes.set_xlim(-0.5, max(len(values) - 0.5, 0.5))
        self.draw_idle()

    def _configure_axes(self):
        self.axes.set_facecolor("#0d1119")
        self.axes.set_title("Uso da CPU", color="#f3f6fb", fontsize=13, loc="left", pad=14)
        self.axes.set_ylabel("Uso (%)", color="#aab4c4")
        self.axes.set_ylim(0, 100)
        self.axes.tick_params(axis="y", colors="#8993a5", labelsize=9)
        self.axes.tick_params(axis="x", bottom=False, labelbottom=False)
        self.axes.grid(axis="y", color="#27303e", linewidth=0.8, alpha=0.8)
        self.axes.grid(axis="x", visible=False)
        for spine in self.axes.spines.values():
            spine.set_color("#27303e")

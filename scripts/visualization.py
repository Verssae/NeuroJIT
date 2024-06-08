from pathlib import Path
import numpy as np

import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path as MatPath
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import matplotlib.font_manager as fm

# See: https://stackoverflow.com/questions/52910187/how-to-make-a-polygon-radar-spider-chart-in-python


def radar_factory(num_vars, frame="circle"):
    """Create a radar chart with `num_vars` axes.

    This function creates a RadarAxes projection and registers it.

    Parameters
    ----------
    num_vars : int
        Number of variables for radar chart.
    frame : {'circle' | 'polygon'}
        Shape of frame surrounding axes.

    """
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            # Paths with non-unit interpolation steps correspond to gridlines,
            # in which case we force interpolation (to defeat PolarTransform's
            # autoconversion to circular arcs).
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return MatPath(self.transform(path.vertices), path.codes)

    class RadarAxes(PolarAxes):
        name = "radar"

        PolarTransform = RadarTransform

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # rotate plot such that the first axis is at the top
            self.set_theta_zero_location("N")

        def fill(self, *args, closed=True, **kwargs):
            """Override fill so that line is closed by default"""
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.concatenate((x, [x[0]]))
                y = np.concatenate((y, [y[0]]))
                line.set_data(x, y)

        def set_varlabels(self, labels):
            return self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
            # in axes coordinates.
            if frame == "circle":
                return Circle((0.5, 0.5), 0.5)
            elif frame == "polygon":
                return RegularPolygon((0.5, 0.5), num_vars, radius=0.5, edgecolor="k")
            else:
                raise ValueError("unknown value for 'frame': %s" % frame)

        def draw(self, renderer):
            """Draw. If frame is polygon, make gridlines polygon-shaped"""
            if frame == "polygon":
                gridlines = self.yaxis.get_gridlines()
                for gl in gridlines:
                    gl.get_path()._interpolation_steps = num_vars
            super().draw(renderer)

        def _gen_axes_spines(self):
            if frame == "circle":
                return super()._gen_axes_spines()
            elif frame == "polygon":
                # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
                spine = Spine(
                    axes=self,
                    spine_type="circle",
                    path=MatPath.unit_regular_polygon(num_vars),
                )
                # unit_regular_polygon gives a polygon of radius 1 centered at
                # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
                # 0.5) in axes coordinates.
                spine.set_transform(
                    Affine2D().scale(0.5).translate(0.5, 0.5) + self.transAxes
                )

                return {"polar": spine}
            else:
                raise ValueError("unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta


def visualize_hmap(corr_matrix, size=6, save_path=None, format="svg"):
    font_files = fm.findSystemFonts(fontpaths=fm.OSXFontDirectories[-1], fontext="ttf")
    font_files = [ f for f in font_files if "LinLibertine" in f]
    for font_file in font_files:
        fm.fontManager.addfont(font_file)
    
    plt.rcParams["font.family"] = "Linux Libertine"

    # plt.figure(figsize=(6, 6))
    plt.figure(figsize=(size, size))

    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    ax = sns.heatmap(
        corr_matrix, annot=False, cmap="coolwarm", mask=mask, vmin=-1, vmax=1, cbar=False, square=True
    )
    labels = list(map(lambda x: x.replace("_", "/"), corr_matrix.columns))

    
    ax.set_yticklabels(labels, rotation=0, fontsize=15)
    ax.set_xticklabels(labels, rotation=90, fontsize=15)

    # ax.xaxis.tick_top()
    # ax.xaxis.set_label_position("top")
    # ax.yaxis.tick_right()
    # ax.yaxis.set_label_position("right")
    
    greys = sns.color_palette("Greys", n_colors=9)
    for i in range(corr_matrix.shape[0]):
        for j in range(corr_matrix.shape[1]):
            value = corr_matrix.iloc[i, j]
            if  i > j:
                ax.text(
                    j + 0.5,
                    i + 0.5,
                    f"{value:.2f}"[2:] if value > 0 else "-" + f"{value:.2f}"[3:],
                    ha="center",
                    va="center",
                    color=greys[4] if abs(value) < 0.5 else greys[7],
                    fontsize=15,
                    # fontweight="bold",
                )
    # plt.title(
    #     title,
    #     pad=10,
    #     fontdict={"fontweight": "bold", "fontfamily": "serif", "fontsize": 25},
    # )
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(exist_ok=True, parents=True)
        plt.savefig(save_path, bbox_inches="tight", dpi=300, format=format)
        print(save_path)
    else:
        plt.show()
    plt.close()

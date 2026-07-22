from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def save_test_plot(fig: Figure, test_path: str, filename: str) -> None:
    output_dir = Path(test_path).parent / "output"
    output_dir.mkdir(exist_ok=True)

    fig.savefig(output_dir / filename)
    plt.close(fig)

import matplotlib.pyplot as plt
import numpy as np

__all__ = ["imshow", "preview_simulation"]


def field2intensity(field):
    return np.real(np.square(field))


def imshow(title, image, ratio=0.25, cmap="jet", **kwargs):
    plt.tick_params(axis="both", which="major", labelsize=8)

    if title:
        plt.title(title)
    plt.imshow(image, cmap=cmap, **kwargs)
    plt.axis("scaled")

    ny, nx = image.shape
    cx, cy = nx // 2, ny // 2
    plt.xlim(cx * (1 - ratio), cx * (1 + ratio))
    plt.ylim(cy * (1 - ratio), cy * ((1 + ratio)))


def preview_simulation(results):
    # slm pattern
    if "slm_pattern" in results:
        title = "Bandlimited"

        plt.figure("Pattern")
        imshow(None, results["slm_pattern"], cmap="binary")
    else:
        title = "Ideal"

    # lateral profile
    plt.figure(f"{title} Lateral Profile", figsize=(8, 8))
    plt.subplot(221)
    imshow("SLM", field2intensity(results["slm_field"]))
    plt.subplot(222)
    imshow("Objective", field2intensity(results["obj_field"]))
    plt.subplot(223)
    imshow("Pre-Mask", field2intensity(results["pre_mask_field"]))
    plt.subplot(224)
    imshow("Post-Mask", field2intensity(results["post_mask_field"]))

    # axial profile
    # TODO

    plt.show()

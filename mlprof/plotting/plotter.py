# coding: utf-8

colors = {"mpl_standard": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
                           "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
          "custom_edgecolor": ["#CC4F1B", "#1B2ACC", "#3F7F4C"],
          "custom_facecolor": ["#FF9848", "#089FFF", "#7EFF99"],
          }


def open_csv_file(path, columns):
    import pandas as pd
    pd_dataset = pd.read_csv(path, delimiter=",", names=columns)

    # or with chunking?
    """
    tp = pd.read_csv(path, delimiter=",", names=columns, iterator=True, chunksize=2000)
    df = pd.concat(tp, ignore_index=True)
    """
    return pd_dataset


def calculate_medians_and_errors_per_batch_size(different_batch_sizes, path):
    """
    Calculate and plot the medians and errors of the runtime per batch size

    Args:
    different_batch_sizes: list(int). The list of different batch sizes to be plotted
    path: str. The path to the csv file containing the results of the measurement.
    """
    import numpy as np

    # open the csv file
    pd_dataset = open_csv_file(path, ["batch_size", "runtimes"])

    # create the arrays to be plotted with median values and up and down errors
    medians = np.empty(len(different_batch_sizes))
    err_down = np.empty(len(different_batch_sizes))
    err_up = np.empty(len(different_batch_sizes))

    for i, batch_size in enumerate(different_batch_sizes):
        runtimes_per_batch_size = pd_dataset.loc[pd_dataset["batch_size"] == batch_size, "runtimes"]
        # mean = np.mean(runtimes_per_batch_size)
        median = np.percentile(runtimes_per_batch_size, 50)
        medians[i] = median
        err_down[i] = abs(np.percentile(runtimes_per_batch_size, 16) - median)
        err_up[i] = abs(np.percentile(runtimes_per_batch_size, 84) - median)
    return medians, err_down, err_up


def apply_individual_customizations(customization_dict, fig, ax):
    """
    Apply the remaining customization parameters from the command line

    Args:
    customization_dict: dict. The dictionary containing the customization parameters
    fig, ax: the matplotlib object to handle figure and axis.
    """
    import matplotlib.pyplot as plt
    if customization_dict["log_y"]:
        plt.yscale("log")


def fill_plot(x, y, yerr_d, yerr_u, filling, color):
    """
    Fill the plots with the measured values and their errors

    Args:
    x: array(float). x-axis values
    y: array(float). y-axis values
    yerr_d: array(float). error down on the y-axis
    yerr_u: array(float). error up on the y-axis
    filling: bool. customizatioon parameter to decide if the errors will be represented as error bars or bands
    color: the colors to use for the plotted values
    """
    import matplotlib.pyplot as plt
    import numpy as np
    if filling:
        p1 = plt.plot(x, y, "-", color=color)
        plt.fill_between(x, y - yerr_d, y + yerr_u, alpha=0.5, facecolor=color)
        p2 = plt.fill(np.NaN, np.NaN, alpha=0.5, color=color)
        legend = (p1[0], p2[0])
    else:
        p = plt.errorbar(x, y,
                        yerr=(yerr_d, yerr_u),
                        capsize=12,
                        marker=".", linestyle="")
        legend = p[0]
    return legend


def plot_batch_size_several_measurements(different_batch_sizes, input_paths, output_path, measurements,
                                        customization_dict):
    """
    General plotting function for runtime plots

    Args:
    different_batch_sizes: list(int). The batch sizes to be used for the x-axis of the plot.
    input_paths: list(str). The paths of the csv files containing the measurement results.
    output_path: str. The path to be used for saving the plot.
    measurements: list(str). The labels of the plot.
    customization_dict: dict. The dictionary containing the customization parameters.
    """
    import matplotlib.pyplot as plt
    import mplhep as hep

    if type(measurements[0]) == str:
        measurements_paths_strs = measurements
        measurements_labels_strs = measurements
    else:
        measurements_paths_strs = ["_".join(measurement) for measurement in measurements]
        measurements_labels_strs = [", ".join(measurement) for measurement in measurements]
    # get the values to be plotted
    plotting_values = {}
    for i, input_path in enumerate(input_paths):
        medians, err_down, err_up = calculate_medians_and_errors_per_batch_size(different_batch_sizes, input_path)
        if customization_dict["bs_normalized"]:
            medians = medians / different_batch_sizes
            err_down = err_down / different_batch_sizes
            err_up = err_up / different_batch_sizes
        plotting_values[measurements_paths_strs[i]] = {"medians": medians, "err_down": err_down, "err_up": err_up}

    # set style and add CMS logo
    hep.set_style(hep.style.CMS)

    # create plot with curves using a single color for each value-error pair
    fig, ax = plt.subplots(1, 1)
    to_legend = []
    for i in range(0, len(measurements_paths_strs)):
        color = next(ax._get_lines.prop_cycler)["color"]
        legend = fill_plot(different_batch_sizes, plotting_values[measurements_paths_strs[i]]["medians"],
                  plotting_values[measurements_paths_strs[i]]["err_down"],
                  plotting_values[measurements_paths_strs[i]]["err_up"], customization_dict["filling"],
                  color)  # colors["mpl_standard"][i])
        to_legend += [legend]
    # create legend
    plt.legend(to_legend, measurements_labels_strs)

    # apply additional parameters and improve plot style
    plt.xscale("log")
    apply_individual_customizations(customization_dict, fig, ax)
    plt.xlabel("Batch size")
    if customization_dict["bs_normalized"]:
        plt.ylabel("Runtime / batch size [ms]")
    else:
        plt.ylabel("runtime [ms]")
    plt.ylim(bottom=0)
    ax.xaxis.set_major_locator(plt.MaxNLocator(len(different_batch_sizes)))
    ax.xaxis.set_minor_locator(plt.NullLocator())
    plt.xticks(different_batch_sizes, different_batch_sizes)

    # choose text to add on the top left of the figure
    hep.cms.text(text="MLProf", loc=0)  # hep.cms.text(text="Simulation, Network test", loc=0)
    hep.cms.lumitext(text=customization_dict["top_right_label"])
    # save plot
    fig.savefig(output_path, bbox_inches="tight")
    plt.close()

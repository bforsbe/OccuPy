from typing import Optional
import typer

from occupy_lib import estimate   # for terminal use

from pkg_resources import get_distribution
__version__ =  get_distribution("occupy").version



def version_callback(value: bool):
    if value:
        print(f"OccuPy: {__version__}")
        raise typer.Exit()

class occupy_options:
    def __init__(self,
        input_map: str = None,
        resolution: float = None,

        amplify: float = 1,
        attenuate: float = 1,
        sigmoid: float = 1,
        pivot: float = 0.01,

        tau: float = None,
        kernel_size: int = None,
        kernel_radius: float = None,
        tile_size: int = None,
        lowpass_input: float = None,
        lowpass_output: float = None,
        exclude_solvent : bool = False,
        max_box: int = 256,
        hedge_confidence: int = None,
        solvent_def: str = None,
        scale_limit: float = 0.05,
        scale_mode: str = None,
        hist_match: bool = False,
        output_map: str = 'out_<input_file_name>',
        plot : bool = False,
        save_all_maps : bool = False,
        chimerax : bool= True,
        chimerax_silent : bool = False,
        show_chimerax : bool = False,
        min_vis_scale: float = 0.2,
        s0 : bool = False,
        lp_scale : bool = None,
        emdb_id : str = None,
        verbose : bool = False,
        help_all : bool = False,
        version : bool = False,
        gui = False
):
        self.input_map = input_map
        self.resolution = resolution
        self.amplify = amplify
        self.attenuate = attenuate
        self.sigmoid = sigmoid
        self.pivot = pivot
        self.tau = tau
        self.kernel_size = kernel_size
        self.kernel_radius = kernel_radius
        self.tile_size = tile_size
        self.lowpass_input = lowpass_input
        self.lowpass_output = lowpass_output
        self.exclude_solvent = exclude_solvent
        self.max_box = max_box
        self.hedge_confidence = hedge_confidence
        self.solvent_def = solvent_def
        self.scale_limit = scale_limit
        self.scale_mode = scale_mode
        self.hist_match = hist_match
        self.output_map = output_map
        self.plot = plot
        self.save_all_maps = save_all_maps
        self.chimerax = chimerax
        self.chimerax_silent = chimerax_silent
        self.show_chimerax = show_chimerax
        self.min_vis_scale = min_vis_scale
        self.s0 = s0
        self.lp_scale = lp_scale
        self.emdb_id = emdb_id
        self.verbose = verbose
        self.help_all = help_all
        self.version = version
        self.gui = gui

def parse_and_run(
        # Basic input --------------------------------------------------------------------------------------------------

        input_map: str = typer.Option(
            None,
            "--input-map", "-i",
            help="Map to estimate [.mrc NxNxN]"
        ),
        resolution: float = typer.Option(
            None,
            "--resolution", "-r",
            help="The lowest resolution of resolvable content input map.",
            min=0.0
        ),
        amplify: float = typer.Option(
            1.0,
            "--amplify", "-am",
            help="Alter partial occupancies, to make more or less equal to full occupancy?",
            min=1.0
        ),
        attenuate: float = typer.Option(
            1.0,
            "--attenuate", "-at",
            help="Attenuate partial occupancies, to weaken lower occupancies",
            min=1.0
        ),
        sigmoid: float = typer.Option(
            1.0,
            help="Power value for sigmoid scale modification [0,1]",
            min=1.0
        ),
        pivot: float = typer.Option(
            0.01,
            help="Threshold scale value for sigmoid scale modification [0,1]",
            min=0.01,
            max=0.99
        ),

        # Specific control ---------------------------------------------------------------------------------------------

        tau: float = typer.Option(
            None,
            "--tau", "-t",
            help="Percentile for scale-estimate normalization",
            min=0.0,
            max=1.0
        ),
        kernel_size: int = typer.Option(
            None,
            "--kernel-size",
            help="Size of the local occupancy estimation kernel [pixels]"
        ),
        kernel_radius: float = typer.Option(
            None,
            "--kernel-radius",
            help="Size of the local occupancy estimation kernel [pixels]"
        ),
        tile_size: int = typer.Option(
            None,
            "--tile-size",
            help="Size of the local region used for scale normalization [pixels]"
        ),
        lowpass_input: float = typer.Option(
            None,
            "--lowpass", "-lp",
            help="Low-pass filter the input map to this resoution prior to scale estimation. Internal default is 6*pixel-size. [Å]"
        ),
        lowpass_output: float = typer.Option(
            None,
            "--lowpass-output",
            help="Optionally low-pass filter the amplified output to this resolution [Å]"
        ),
        exclude_solvent: bool = typer.Option(
            False,
            "--exclude-solvent/--retain-solvent",
            help="Should Estimated solvent be eliminated [flattened to 0]?"
        ),
        max_box: int = typer.Option(
            256,
            help="Input maps beyond this size will be down-sampled during estimation [pixels]"
        ),
        hedge_confidence: int = typer.Option(
            None,
            help="Exponent order for confidence estimation, such that values > 1 are more careful when amplifying low occupancies"
        ),
        solvent_def: str = typer.Option(
            None,
            help="Mask that defines non-solvent, used to aid solvent model fitting. [.mrc NxNxN]"
        ),
        scale_limit: float = typer.Option(
            0.05,
            "--scale-limit",
            help="Hard limit below which map scale/occupancy will be considered unreliable for amplification",
            min=0.0,
            max=1.0
        ),
        hist_match: bool = typer.Option(
            False,
            help="Histogram-match output (force equal greyscale as input)"
        ),

        # Output control -----------------------------------------------------------------------------------------------

        output_map: str = typer.Option(
            "out_<input_file_name>",
            "--output-map", "-o",
            help="Output map name"
        ),
        plot: bool = typer.Option(
            False,
            help="Plot a histogram showing solvent model fit and occupancy confidence?"
        ),
        save_all_maps: bool = typer.Option(
            False,
            help="Save all maps used internally"
        ),
        chimerax: bool = typer.Option(
            True,
            help="Write a .cxc file that starts an interactive chimeraX session with colored input/output maps"
        ),
        chimerax_silent: bool = typer.Option(
            False,
            help="Write a .cxc file that can be opened by chimeraX to show colored input/output maps"
        ),
        show_chimerax: bool = typer.Option(
            False,
            help="Open chimeraX when done. Implies --chimerax"
        ),
        min_vis_scale: float = typer.Option(
            0.2,
            help="Lower limit of map scale (occupancy) in chimeraX coloring & color-key",
            min=0.0,
            max=1.0
        ),

        # Extra  -------------------------------------------------------------------------------------------------------
        s0: bool = typer.Option(
            False,
            "--S0/--SW",
            help="Use simple kernel normalization S0 instead of tile-based percentile (SW)"
        ),
        lp_scale: bool = typer.Option(
            False,
            "--lp-scale/--raw-scale","--occupancy",
            help="Use the low-passed input for scale estimation, or use the raw input map"
        ),
        emdb_id: str = typer.Option(
            None,
            "--emdb","--emdb-id",
            help="Fetch the main map from an EMDB entry and use as input"
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose/--quiet",
            help="Let me know what's going on"
        ),
        #relion_classes: str = typer.Option(
        #    None,
        #    help="File of classes to diversify by occupancy amplification [_model.star]"
        #),
        help_all: Optional[bool] = typer.Option(
            None,
            "--help-all",
            is_eager=True,
            help="Print lots of help and exit"
        ),
        version: Optional[bool] = typer.Option(
            None,
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Print version info and exit"
        )
):
    scale_mode = 'res'
    if lp_scale:
        scale_mode = 'occ'

    options = occupy_options(
        input_map,
        resolution,
        amplify,
        attenuate,
        sigmoid,
        pivot,
        tau,
        kernel_size,
        kernel_radius,
        tile_size,
        lowpass_input,
        lowpass_output,
        exclude_solvent,
        max_box,
        hedge_confidence,
        solvent_def,
        scale_limit,
        scale_mode,
        hist_match,
        output_map,
        plot,
        save_all_maps,
        chimerax,
        chimerax_silent,
        show_chimerax,
        min_vis_scale,
        s0,
        lp_scale,
        emdb_id,
        verbose,
        help_all,
        version
    )

    estimate.occupy_run(options)

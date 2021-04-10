# This file is part of gwe.
#
# Copyright (c) 2018 Roberto Leinardi
#
# gwe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwe.  If not, see <http://www.gnu.org/licenses/>.

from typing import Optional, Any, Dict, Tuple
from gi.repository import Gio, GLib, Gtk, Gdk
from matplotlib.axes import Axes
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.colors import ColorConverter
from matplotlib.figure import Figure

from gwe.conf import MIN_TEMP, MAX_TEMP, FAN_MAX_DUTY, GRAPH_COLOR_HEX
from gwe.model.fan_profile import FanProfile


def build_glib_option(long_name: str,
                      short_name: Optional[str] = None,
                      flags: int = 0,
                      arg: int = GLib.OptionArg.NONE,
                      arg_data: Optional[object] = None,
                      description: Optional[str] = None,
                      arg_description: Optional[str] = None) -> GLib.OptionEntry:
    option = GLib.OptionEntry()
    option.long_name = long_name
    option.short_name = 0 if not short_name else ord(short_name[0])
    option.flags = flags
    option.description = description
    option.arg = arg
    option.arg_description = arg_description
    option.arg_data = arg_data
    return option


def hide_on_delete(widget: Gtk.Widget, *_: Any) -> Any:
    widget.hide()
    return widget.hide_on_delete()


def rgba_to_hex(color: Gdk.RGBA) -> str:
    """Return hexadecimal string for :class:`Gdk.RGBA` `color`."""
    return "#{0:02x}{1:02x}{2:02x}{3:02x}".format(int(color.red * 255),
                                                  int(color.green * 255),
                                                  int(color.blue * 255),
                                                  int(color.alpha * 255))


def init_plot_chart(scrolled_window: Gtk.ScrolledWindow,
                    figure: Figure,
                    canvas: FigureCanvas,
                    axis: Axes) -> Tuple:
    axis.patch.set_visible(False)
    temp_window = Gtk.Window()
    style = temp_window.get_style_context()
    bg_colour = style.get_background_color(Gtk.StateType.NORMAL).to_color().to_floats()
    cc = ColorConverter()
    cc.to_rgba(bg_colour)
    figure.patch.set_facecolor(bg_colour)

    axis.grid(True, linestyle=':')
    axis.margins(x=0, y=0.05)

    temp_label = Gtk.Label()
    scrolled_window.add(temp_label)
    text_color = rgba_to_hex(temp_label.get_style_context().get_color(Gtk.StateType.NORMAL))
    text_color_alpha = text_color[:-2] + '80'
    scrolled_window.remove(temp_label)
    axis.set_xlabel('Temperature [°C]', color=text_color)
    axis.set_ylabel('Duty [%]', color=text_color)
    axis.tick_params(colors=text_color, grid_color=text_color_alpha)
    for spine in axis.spines.values():
        spine.set_edgecolor(text_color_alpha)
    figure.subplots_adjust(top=1)
    canvas.set_size_request(400, 300)
    scrolled_window.add_with_viewport(canvas)
    # Returns a tuple of line objects, thus the comma
    growing_line = axis.plot(
        [],
        [],
        'o-',
        linewidth=3.0,
        markersize=10,
        antialiased=True,
        color=GRAPH_COLOR_HEX
    )
    decreasing_line = axis.plot(
        [],
        [],
        ':',
        linewidth=2.0,
        antialiased=True,
        color=GRAPH_COLOR_HEX,
        alpha=0.66
    )
    axis.set_ybound(lower=-5, upper=105)
    axis.set_xbound(MIN_TEMP, MAX_TEMP)
    figure.canvas.draw()
    return growing_line[0], decreasing_line[0]


def get_fan_profile_data(profile: FanProfile) -> Dict[int, int]:
    data = {p.temperature: p.duty for p in profile.steps}
    if data:
        # if profile.single_step:
        #     data.update({MAX_TEMP: profile.steps[0].duty})
        # else:
        if MIN_TEMP not in data:
            data[MIN_TEMP] = data[min(data.keys())]
        data.update({MAX_TEMP: FAN_MAX_DUTY})
    return data


def is_dazzle_version_supported() -> bool:
    if Gtk.MAJOR_VERSION >= 3 and Gtk.MINOR_VERSION >= 24:  # Mypy says that this check returns Any, not sure why...
        return True
    return False


def get_default_application() -> Gtk.Application:
    return Gtk.Application.get_default()


def show_notification(summary: str, body: str, iconname: str) -> None:
    application = get_default_application()
    notification = Gio.Notification.new(title=summary)
    notification.set_body(body)
    iconname = Gio.ThemedIcon.new(iconname=iconname)
    notification.set_icon(iconname)
    application.send_notification(None, notification)


def open_uri(uri: str, parent: Gtk.Window = None, timestamp: int = Gdk.CURRENT_TIME) -> None:
    Gtk.show_uri_on_window(parent, uri, timestamp)

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import svgwrite
import threading
import numpy as np
import os

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gst, GstBase, Gtk

GObject.threads_init()
Gst.init(None)


class GstPipeline:
    def __init__(self, pipeline, user_function, src_size):
        self.user_function = user_function
        self.running = False
        self.gstbuffer = None
        self.sink_size = None
        self.src_size = src_size
        self.box = None
        self.condition = threading.Condition()
        self.latest_frame = None

        self.pipeline = Gst.parse_launch(pipeline)
        # self.overlay = self.pipeline.get_by_name('overlay')
        # self.overlaysink = self.pipeline.get_by_name('overlaysink')
        appsink = self.pipeline.get_by_name('appsink')
        appsink.connect('new-sample', self.on_new_sample)

        # Set up a pipeline bus watch to catch errors.
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

        # Set up a full screen window on Coral, no-op otherwise.
        # self.setup_window()

    def run(self):
        # Start inference worker.
        self.running = True
        # worker = threading.Thread(target=self.inference_loop)
        worker = threading.Thread(target=self.frame_pass_on)
        worker.start()

        # Run pipeline.
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except:
            pass

        # Clean up.
        self.pipeline.set_state(Gst.State.NULL)
        while GLib.MainContext.default().iteration(False):
            pass
        with self.condition:
            self.running = False
            self.condition.notify_all()
        worker.join()

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            Gtk.main_quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write('Warning: %s: %s\n' % (err, debug))
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write('Error: %s: %s\n' % (err, debug))
            Gtk.main_quit()
        return True

    def on_new_sample(self, sink):
        sample = sink.emit('pull-sample')
        # if not self.sink_size:
        s = sample.get_caps().get_structure(0)
        height = s.get_value('height')
        width = s.get_value('width')
        self.sink_size = (width, height)
        with self.condition:
            self.gstbuffer = sample.get_buffer()
            # Get read access to the buffer data
            success, map_info = self.gstbuffer.map(Gst.MapFlags.READ)
            if not success:
                raise RuntimeError("Could not map buffer data!")

            self.latest_frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=map_info.data)

            # Clean up the buffer mapping
            self.gstbuffer.unmap(map_info)
            self.condition.notify_all()

        return Gst.FlowReturn.OK

    def frame_pass_on(self):
        while True:
            with self.condition:
                while not self.gstbuffer and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstbuffer = self.gstbuffer
                self.gstbuffer = None

            self.user_function(self.latest_frame)


def detectCoralDevBoard():
    try:
        if 'MX8MQ' in open('/sys/firmware/devicetree/base/model').read():
            print('Detected Edge TPU dev board.')
            return True
    except:
        pass
    return False


def setup_pipeline(user_function,
                   src_size,
                   appsink_size,
                   videosrc='/dev/video1',
                   videofmt='raw'):
    if videofmt == 'h264':
        SRC_CAPS = 'video/x-h264,width={width},height={height},framerate=30/1'
    elif videofmt == 'jpeg':
        SRC_CAPS = 'image/jpeg,width={width},height={height},framerate=30/1'
    else:
        SRC_CAPS = 'video/x-raw,width={width},height={height},framerate=30/1'
    if videosrc.startswith('/dev/video'):
        PIPELINE = 'v4l2src device=%s ! {src_caps}' % videosrc
    elif videosrc.startswith('http'):
        PIPELINE = 'souphttpsrc location=%s' % videosrc
    elif videosrc.startswith('rtsp'):
        PIPELINE = 'rtspsrc location=%s' % videosrc
    else:
        demux = 'avidemux' if videosrc.endswith('avi') else 'qtdemux'
        PIPELINE = """filesrc location=%s ! %s name=demux  demux.video_0
                    ! queue ! decodebin  ! videorate
                    ! videoconvert n-threads=4 ! videoscale n-threads=4
                    ! {src_caps} ! {leaky_q} """ % (videosrc, demux)

    if detectCoralDevBoard():
        scale_caps = None
        PIPELINE += """ ! decodebin ! glupload ! tee name=t
            t. ! queue ! glfilterbin filter=glbox name=glbox ! {sink_caps} ! {sink_element}
        """
    else:
        scale = min(appsink_size[0] / src_size[0], appsink_size[1] / src_size[1])
        scale = tuple(int(x * scale) for x in src_size)
        scale_caps = 'video/x-raw,width={width},height={height}'.format(width=scale[0], height=scale[1])
        PIPELINE += """ ! tee name=t
            t. ! {leaky_q} ! videoconvert ! videoscale ! {scale_caps} ! videobox name=box autocrop=true
               ! {sink_caps} ! {sink_element}
            t. ! {leaky_q} ! videoconvert
               ! rsvgoverlay name=overlay ! videoconvert ! ximagesink sync=false
            """

    SINK_ELEMENT = 'appsink name=appsink emit-signals=true max-buffers=1 drop=true'
    SINK_CAPS = 'video/x-raw,format=RGB,width={width},height={height}'
    LEAKY_Q = 'queue max-size-buffers=1 leaky=downstream'

    src_caps = SRC_CAPS.format(width=src_size[0], height=src_size[1])
    sink_caps = SINK_CAPS.format(width=appsink_size[0], height=appsink_size[1])
    pipeline = PIPELINE.format(leaky_q=LEAKY_Q,
                               src_caps=src_caps, sink_caps=sink_caps,
                               sink_element=SINK_ELEMENT, scale_caps=scale_caps)

    print('Gstreamer pipeline:\n', pipeline)

    os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
    pipeline = GstPipeline(pipeline, user_function, src_size)

    return pipeline

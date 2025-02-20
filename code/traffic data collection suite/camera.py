import gi
import numpy as np
import cv2
from gi.repository import Gst, GLib
import time

from yolov5Detector import Yolov5Detector



Gst.init(None)

def gst_to_opencv(sample):
    """Convert GStreamer sample to OpenCV image"""
    buf = sample.get_buffer()
    caps = sample.get_caps()
    
    height = caps.get_structure(0).get_int('height')[1]
    width = caps.get_structure(0).get_int('width')[1]
    
    # Extract frame data
    success, map_info = buf.map(Gst.MapFlags.READ)
    if not success:
        return None
    
    # Convert to numpy array
    frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 4))
    buf.unmap(map_info)
    return frame

class CSI_Camera:
    def __init__(self):
        self.pipeline = Gst.parse_launch(
            "nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=1920, height=1080 ! nvvidconv ! video/x-raw, format=RGBA ! appsink name=appsink emit-signals=true max-buffers=1 drop=true"
        )
        self.det = Yolov5Detector()

        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.connect("new-sample", self.on_new_sample)
        self.latest_frame = None
    
    def on_new_sample(self, sink):
        """Callback when a new frame is available"""
        sample = sink.emit("pull-sample")
        frame = gst_to_opencv(sample)
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            frame = self.det.infere(frame)
            self.latest_frame = frame
        return Gst.FlowReturn.OK
    
    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)
    
    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
    
    def get_latest_frame(self):
        return self.latest_frame

if __name__ == "__main__":
    cam = CSI_Camera()
    cam.start()
    
    try:
        while True:
            frame = cam.get_latest_frame()
            if frame is not None:
                #frame = frame[:,:,:3]
                

                cv2.imwrite("image.jpeg", frame)
                print("frame")

            #time.sleep(0.033)
            

    except KeyboardInterrupt:
        pass
    
    cam.stop()
    cv2.destroyAllWindows()
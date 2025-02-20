import base64
import signal
import time

import cv2
import numpy as np
from fastapi import Response

from nicegui import Client, app, core, run, ui
from nicegui import ui

import datetime as dt
from datetime import datetime

from camera import CSI_Camera

def convert(frame: np.ndarray) -> bytes:
    """Converts a frame from OpenCV to a JPEG image.

    This is a free function (not in a class or inner-function),
    to allow run.cpu_bound to pickle it and send it to a separate process.
    """
    _, imencode_image = cv2.imencode('.jpg', frame)
    return imencode_image.tobytes()


@app.get('/video/frame')
# Thanks to FastAPI's `app.get` it is easy to create a web route which always provides the latest image from OpenCV.
async def grab_video_frame() -> Response:
    frame = camera.get_latest_frame()
    if(type(frame) != type(None)):
        # `convert` is a CPU-intensive function, so we run it in a separate process to avoid blocking the event loop and GIL.
        jpeg = await run.cpu_bound(convert, frame)
        return Response(content=jpeg, media_type='image/jpeg')
    else:
        print("image is none")
        black_1px = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjYGBg+A8AAQQBAHAgZQsAAAAASUVORK5CYII='
        placeholder = Response(content=base64.b64decode(black_1px.encode('ascii')), media_type='image/png')
        return placeholder

with ui.card():
    video_image = ui.interactive_image(size=(720, 480))
    ui.timer(interval=0.1, callback=lambda: video_image.set_source(f'/video/frame?{time.time()}'))

    #ui.html('<iframe src="http://wp.pl" width="720" height="400" frameborder="0"></iframe>')
    #ui.element('iframe').props('src="https://nicegui.io" sandbox').classes('w-full h-[calc(100vh-3em)]')

    #ui.html('''
    #<iframe src="https://example.com" width="720px" height="400px" style="border:none;"></iframe>
    #''')
    with ui.element('iframe').classes('w-full h-[600px] border-0') as iframe:
        iframe.props('src="http://harold:3000/public-dashboards/1a9dd83e36fe4915a3581dc09319a6b4?orgId=1&from=now-15m&to=now&timezone=browser&refresh=auto"')

    #ui.element('iframe').props('src="http://nicegui.io" sandbox').classes('w-full h-[calc(100vh-3em)]')

    dark = ui.dark_mode()
    dark.enable()
    echart = ui.echart({
        'xAxis': {'type': 'category'},
        'yAxis': {'type': 'value', 'data': ['samochody w ostatniej godzinie'], 'inverse': False},
        'legend': {'textStyle': {'color': 'gray'}},
        'series': [
            {'type': 'bar', 'name': 'Cars seen in hours', 'data': [0]*24},
        ],
    })



    line_plot24 = ui.line_plot(n=1, limit=24, figsize=(8, 7), update_every=1) \
        .with_legend(['number of seen cars'], loc='upper center', ncol=1)

    line_plot24_const = ui.line_plot(n=1, limit=24, figsize=(8, 7), update_every=1) \
        .with_legend(['number of seen cars'], loc='upper center', ncol=1)

    line_plot24.visible = False
    line_plot24_const.visible = False

    echart.visible = False

ui.run()

camera = CSI_Camera()



def update_line_plot() -> None:
    camera.det.eventCollector.maybePush()
    return
    eventFilter = camera.det.eventCollector.eventFilter

    keys = []
    values = []
    line_plot24.clear()
    #for i in range(60):
    #    keys.append(-59+i)
    #    now = datetime.now() - dt.timedelta(minutes=(59-i))
    #    then = now - dt.timedelta(minutes=1)
    #    events = eventFilter.getLast10Minutes(now, then)
    #    values.append(len(events))
    #    line_plot.push([-59+i], [[len(events)]])

    #for i in range(24):
            #keys.append(-24+i)
            #now = datetime.now() - dt.timedelta(hours=(24-i))
            #then = now - dt.timedelta(hours=1)
            #events = eventFilter.getLast10Minutes(now, then)
            #values.append(len(events))
            #line_plot24.push([-24+i], [[len(events)]])

    for i in range(24):
            keys.append(-24+i)
            now = datetime.now()
            now = now - dt.timedelta(minutes=now.minute, seconds=now.second)

            now = now - dt.timedelta(hours=(24-i))
            then = now - dt.timedelta(hours=1)
            events = eventFilter.getLast10Minutes(now, then)
            values.append(len(events))
            #line_plot24_const.push([now.hour], [[len(events)]])
            echart.options['series'][0]['data'][(now.hour+1)%24] = len(events)

    #print("trying to add k, v to plot ", keys, values)

    
    


line_updates = ui.timer(15, update_line_plot, active=True)

camera.start()
ui.run(reload=False)



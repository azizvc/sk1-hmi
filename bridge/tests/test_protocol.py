from sk1_hmi.hmi.protocol import FrameBuffer, HmiEventKind, encode_command, parse_frame


def test_encode_command():
    assert encode_command("page 0").endswith(b"\xff\xff\xff")


def test_parse_touch():
    ev = parse_frame(bytes([0x65, 0, 10, 1]))
    assert ev is not None
    assert ev.kind == HmiEventKind.TOUCH
    assert ev.page == 0
    assert ev.component == 10


def test_frame_buffer_init_and_touch():
    fb = FrameBuffer()
    events = fb.feed(b"\x91")
    assert events[0].kind == HmiEventKind.INIT
    events = fb.feed(bytes([0x65, 1, 5, 1]) + b"\xff\xff\xff")
    assert events[0].kind == HmiEventKind.TOUCH
    assert events[0].page == 1
